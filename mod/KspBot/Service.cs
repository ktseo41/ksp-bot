using System;
using System.Collections.Generic;
using System.Linq;
using KRPC.Service;
using KRPC.Service.Attributes;
using UnityEngine;

namespace KspBot
{
    /// <summary>
    /// Career helpers that kRPC lacks: tech research, facility upgrades, part catalog, craft building.
    /// All complex results are JSON strings.
    /// </summary>
    [KRPCService(Name = "KspBot", GameScene = GameScene.All)]
    public static class KspBotService
    {
        /// <summary>Scene, save and currencies.</summary>
        [KRPCProcedure]
        public static string Status()
        {
            var o = new Obj
            {
                ["scene"] = HighLogic.LoadedScene.ToString(),
                ["save"] = HighLogic.SaveFolder,
                ["mode"] = HighLogic.CurrentGame?.Mode.ToString(),
                ["ut"] = Planetarium.GetUniversalTime(),
            };
            if (Funding.Instance != null) o["funds"] = Funding.Instance.Funds;
            if (ResearchAndDevelopment.Instance != null) o["science"] = ResearchAndDevelopment.Instance.Science;
            if (Reputation.Instance != null) o["reputation"] = Reputation.Instance.reputation;
            return Json.Write(o);
        }

        /// <summary>Close popup dialogs (e.g. the expansion ad shown at flight start). Returns how many.</summary>
        [KRPCProcedure]
        public static int DismissDialogs()
        {
            var dialogs = UnityEngine.Object.FindObjectsOfType<PopupDialog>();
            foreach (var d in dialogs) d.Dismiss();
            return dialogs.Length;
        }

        /// <summary>CommNet "Require Signal for Control" (difficulty option) for the current game; saved at once.</summary>
        [KRPCProcedure]
        public static bool SetRequireSignal(bool on)
        {
            var p = HighLogic.CurrentGame.Parameters.CustomParams<CommNet.CommNetParams>();
            p.requireSignalForControl = on;
            GamePersistence.SaveGame("persistent", HighLogic.SaveFolder, SaveMode.OVERWRITE);
            return p.requireSignalForControl;
        }

        /// <summary>Set a vessel's type (like the stock rename dialog). kRPC hides type Unknown vessels, e.g. a
        /// contract's "Module 761V7" to recover; as a Probe it can be targeted. Returns how many were changed.</summary>
        [KRPCProcedure]
        public static int SetVesselType(string name, string type)
        {
            var t = (VesselType)Enum.Parse(typeof(VesselType), type, true);
            var n = 0;
            foreach (var v in FlightGlobals.Vessels.Where(v => v.vesselName == name))
            {
                v.vesselType = t;
                if (v.protoVessel != null) v.protoVessel.vesselType = t;
                n++;
            }
            GameEvents.onVesselRename.Fire(new GameEvents.HostedFromToAction<Vessel, string>(null, name, name));
            return n;
        }

        /// <summary>Klaw diagnostics for the active vessel: grapple state, arm animation progress, where the capture
        /// ray starts (claw part frame), and what that ray hits with the Klaw's own layer mask vs all layers.</summary>
        [KRPCProcedure]
        public static string GrappleDebug(string targetName)
        {
            var v = FlightGlobals.ActiveVessel;
            var g = v.FindPartModulesImplementing<ModuleGrappleNode>().FirstOrDefault()
                    ?? throw new InvalidOperationException("no Klaw");
            var nt = g.nodeTransform;
            var anim = typeof(ModuleGrappleNode).GetField("deployAnimator", Any)?.GetValue(g) as ModuleAnimateGeneric;
            var pt = g.part.transform;
            var o = new Obj
            {
                ["state"] = g.state,
                ["fsm"] = (typeof(ModuleGrappleNode).GetField("fsm", Any)?.GetValue(g) as KerbalFSM)?.currentStateName,
                ["progress"] = anim != null ? (object)anim.Progress : null,
                ["node"] = pt.InverseTransformPoint(nt.position).ToString("F3"),
                ["nodeFwd"] = pt.InverseTransformDirection(nt.forward).ToString("F3"),
                ["range"] = g.captureRange, ["minDot"] = g.captureMinFwdDot, ["maxRvel"] = g.captureMaxRvel,
                ["grappleNode"] = typeof(ModuleGrappleNode).GetField("grappleNode", Any)?.GetValue(g) != null,
            };
            RaycastHit h;
            if (Physics.Raycast(nt.position, nt.forward, out h, 50f, LayerUtil.DefaultEquivalent))
            {
                var p = FlightGlobals.GetPartUpwardsCached(h.transform.gameObject);
                o["hitMask"] = $"{p?.partInfo.title} on {p?.vessel.vesselName} at {h.distance:F3} m, dot {Vector3.Dot(nt.forward, -h.normal):F3}, layer {h.collider.gameObject.layer}";
            }
            if (Physics.Raycast(nt.position, nt.forward, out h, 50f))
            {
                var p = FlightGlobals.GetPartUpwardsCached(h.transform.gameObject);
                o["hitAll"] = $"{p?.partInfo.title} on {p?.vessel.vesselName} at {h.distance:F3} m, layer {h.collider.gameObject.layer} ({LayerMask.LayerToName(h.collider.gameObject.layer)})";
            }
            var tv = FlightGlobals.VesselsLoaded.FirstOrDefault(x => x.vesselName == targetName);
            if (tv != null)
                o["targetColliders"] = string.Join("; ", tv.parts.SelectMany(p => p.GetComponentsInChildren<Collider>(true))
                    .Select(c => $"{c.name} layer {c.gameObject.layer} ({LayerMask.LayerToName(c.gameObject.layer)}) trigger {c.isTrigger} enabled {c.enabled} {c.GetType().Name}"));
            o["mask"] = LayerUtil.DefaultEquivalent;
            // The pieces of ModuleGrappleNode.on_contact's condition (Rescue 3: ray at 0.010 m, dot 1.000, still Ready)
            var t = typeof(ModuleGrappleNode);
            try
            {
                var other = t.GetField("otherPart", Any)?.GetValue(g) as Part;
                o["otherPart"] = other == null ? "null" : $"{other.partInfo.title} on {other.vessel.vesselName}";
                if (t.GetField("hit", Any)?.GetValue(g) is RaycastHit fh)
                    o["hitField"] = $"{fh.distance:F3} m, point-node {(nt.position - fh.point).magnitude:F3} m";
                var adj = t.GetField("adjusterCache", Any)?.GetValue(g) as System.Collections.IList;
                o["adjusters"] = adj?.Count;
                o["adjusterBlocks"] = t.GetMethod("IsAdjusterBlockingGrappleGrab", Any)?.Invoke(g, null);
                o["klawRb"] = g.part.rb == null ? "null" : g.part.rb.velocity.ToString("F3");
                o["packed"] = g.part.packed;
                if (other != null)
                {
                    o["otherRb"] = other.Rigidbody == null ? "null" : other.Rigidbody.velocity.ToString("F3");
                    if (g.part.rb != null && other.Rigidbody != null)
                        o["rvel"] = (g.part.rb.velocity - other.Rigidbody.velocity).magnitude;
                }
                var fsm = t.GetField("fsm", Any)?.GetValue(g) as KerbalFSM;
                var ev = t.GetField("on_contact", Any)?.GetValue(g) as KFSMEvent;
                if (ev != null && fsm != null)
                {
                    o["contactInState"] = fsm.CurrentState?.StateEvents?.Contains(ev);
                    try { o["contactCondition"] = ev.OnCheckCondition?.Invoke(fsm.CurrentState); }
                    catch (Exception ex) { o["contactCondition"] = "threw " + ex.GetType().Name + ": " + ex.Message; }
                }
            }
            catch (Exception ex) { o["condError"] = ex.GetType().Name + ": " + ex.Message; }
            return Json.Write(o);
        }

        /// <summary>Show a message on the game screen.</summary>
        [KRPCProcedure]
        public static void Message(string text, float seconds)
        {
            ScreenMessages.PostScreenMessage(text, seconds, ScreenMessageStyle.UPPER_CENTER);
        }

        /// <summary>KSP's own flight event log (collisions, explosions, overheating, staging) from index `start`.</summary>
        [KRPCProcedure]
        public static IList<string> FlightEvents(int start)
        {
            var log = FlightLogger.eventLog;
            if (log == null || start >= log.Count) return new List<string>();
            return log.Skip(Math.Max(0, start)).ToList();
        }

        /// <summary>TEST ONLY (sandbox saves): put the active vessel on a circular orbit.</summary>
        [KRPCProcedure]
        public static void SandboxSetOrbit(string body, double altitude, double inclination)
        {
            if (HighLogic.CurrentGame.Mode != Game.Modes.SANDBOX)
                throw new InvalidOperationException("SandboxSetOrbit is only allowed in sandbox saves");
            var b = FlightGlobals.Bodies.FirstOrDefault(x => x.bodyName == body) ?? throw new ArgumentException("unknown body");
            FlightGlobals.fetch.SetShipOrbit(b.flightGlobalsIndex, 0, b.Radius + altitude, inclination, 0, 0, 0, 0);
        }

        // ---------------- Tech tree ----------------

        static bool Researched(string techId) =>
            ResearchAndDevelopment.GetTechnologyState(techId) == RDTech.State.Available;

        static bool ParentsOk(ProtoRDNode n)
        {
            if (n.parents == null || n.parents.Count == 0) return true;
            return n.AnyParentToUnlock
                ? n.parents.Any(p => Researched(p.tech.techID))
                : n.parents.All(p => Researched(p.tech.techID));
        }

        /// <summary>All tech nodes: id, title, cost, researched, researchable, parents, parts.</summary>
        [KRPCProcedure]
        public static string TechTree()
        {
            var parts = PartLoader.LoadedPartsList;
            var list = new List<object>();
            foreach (var n in AssetBase.RnDTechTree.GetTreeNodes())
            {
                var id = n.tech.techID;
                list.Add(new Obj
                {
                    ["id"] = id,
                    ["title"] = ResearchAndDevelopment.GetTechnologyTitle(id),
                    ["cost"] = n.tech.scienceCost,
                    ["researched"] = Researched(id),
                    ["researchable"] = !Researched(id) && ParentsOk(n),
                    ["anyParent"] = n.AnyParentToUnlock,
                    ["parents"] = n.parents.Select(p => p.tech.techID).ToList(),
                    ["parts"] = parts.Where(p => p.TechRequired == id && p.category != PartCategories.none)
                        .Select(p => p.name).ToList(),
                });
            }
            return Json.Write(list);
        }

        /// <summary>Research a tech node, paying science like the R&amp;D building does.</summary>
        [KRPCProcedure]
        public static string Research(string techId)
        {
            var n = AssetBase.RnDTechTree.GetTreeNodes().FirstOrDefault(x => x.tech.techID == techId);
            if (n == null) throw new ArgumentException("unknown tech " + techId);
            if (Researched(techId)) throw new InvalidOperationException("already researched");
            if (!ParentsOk(n)) throw new InvalidOperationException("parent techs not researched");
            var rd = ResearchAndDevelopment.Instance;
            var cost = n.tech.scienceCost;
            if (rd.Science < cost) throw new InvalidOperationException($"not enough science ({rd.Science:F1} < {cost})");
            var limit = GameVariables.Instance.GetScienceCostLimit(
                ScenarioUpgradeableFacilities.GetFacilityLevel(SpaceCenterFacility.ResearchAndDevelopment));
            if (cost > limit) throw new InvalidOperationException($"R&D level allows nodes up to {limit} science");
            rd.AddScience(-cost, TransactionReasons.RnDTechResearch);
            rd.UnlockProtoTechNode(n.tech);
            ResearchAndDevelopment.RefreshTechTreeUI();
            GamePersistence.SaveGame("persistent", HighLogic.SaveFolder, SaveMode.OVERWRITE);
            return Json.Write(new Obj { ["researched"] = techId, ["science"] = rd.Science });
        }

        // ---------------- Parts ----------------

        internal static bool PartUsable(AvailablePart ap) =>
            HighLogic.CurrentGame == null || HighLogic.CurrentGame.Mode != Game.Modes.CAREER ||
            ResearchAndDevelopment.PartModelPurchased(ap);

        /// <summary>Part catalog with the stats needed for design. onlyUsable: only researched parts.</summary>
        [KRPCProcedure]
        public static string Parts(bool onlyUsable)
        {
            var list = new List<object>();
            foreach (var ap in PartLoader.LoadedPartsList)
            {
                if (ap.category == PartCategories.none || ap.partPrefab == null) continue;
                if (onlyUsable && !PartUsable(ap)) continue;
                var p = ap.partPrefab;
                var o = new Obj
                {
                    ["name"] = ap.name,
                    ["title"] = ap.title,
                    ["category"] = ap.category.ToString(),
                    ["tech"] = ap.TechRequired,
                    ["usable"] = PartUsable(ap),
                    ["cost"] = ap.cost,
                    ["dryMass"] = p.mass,
                    ["crew"] = p.CrewCapacity,
                    ["stackNodes"] = p.attachNodes.Select(a => a.id + ":" + a.size).ToList(),
                    ["srfAttachable"] = p.attachRules.srfAttach,
                    ["allowsSrfAttachOnIt"] = p.attachRules.allowSrfAttach,
                    ["modules"] = p.Modules.Cast<PartModule>().Select(m => m.moduleName).Distinct().ToList(),
                };
                var res = new Obj();
                double wet = p.mass;
                foreach (var r in p.Resources)
                {
                    res[r.resourceName] = r.maxAmount;
                    wet += r.amount * r.info.density;
                }
                if (res.Count > 0) o["resources"] = res;
                o["wetMass"] = wet;
                var engines = p.FindModulesImplementing<ModuleEngines>();
                if (engines.Count > 0)
                {
                    var e = engines[0];
                    o["engine"] = new Obj
                    {
                        ["thrust"] = e.maxThrust,
                        ["ispVac"] = e.atmosphereCurve.Evaluate(0f),
                        ["ispAsl"] = e.atmosphereCurve.Evaluate(1f),
                        ["throttleable"] = !e.throttleLocked,
                        ["propellants"] = e.propellants.Select(x => x.name + ":" + x.ratio).ToList(),
                        ["gimbal"] = p.FindModuleImplementing<ModuleGimbal>()?.gimbalRange ?? 0f,
                    };
                }
                var exp = p.FindModulesImplementing<ModuleScienceExperiment>();
                if (exp.Count > 0) o["experiments"] = exp.Select(x => x.experimentID).ToList();
                list.Add(o);
            }
            return Json.Write(list);
        }

        // ---------------- Facilities ----------------

        static float Lvl(SpaceCenterFacility f) => ScenarioUpgradeableFacilities.GetFacilityLevel(f);

        /// <summary>Facility levels, upgrade costs (space center only) and the limits they impose.</summary>
        [KRPCProcedure]
        public static string Facilities()
        {
            var facs = new List<object>();
            foreach (var kv in ScenarioUpgradeableFacilities.protoUpgradeables)
            {
                var count = ScenarioUpgradeableFacilities.GetFacilityLevelCount(kv.Key);
                if (count <= 0) continue;
                var norm = ScenarioUpgradeableFacilities.GetFacilityLevel(kv.Key);
                var o = new Obj
                {
                    ["id"] = kv.Key,
                    ["level"] = Mathf.RoundToInt(norm * count) + 1,
                    ["maxLevel"] = count + 1,
                };
                var fac = kv.Value.facilityRefs?.FirstOrDefault();
                if (fac != null && fac.FacilityLevel < fac.MaxLevel) o["upgradeCost"] = fac.GetUpgradeCost();
                facs.Add(o);
            }
            var gv = GameVariables.Instance;
            var vab = Lvl(SpaceCenterFacility.VehicleAssemblyBuilding);
            var pad = Lvl(SpaceCenterFacility.LaunchPad);
            var mc = Lvl(SpaceCenterFacility.MissionControl);
            var ts = Lvl(SpaceCenterFacility.TrackingStation);
            var ac = Lvl(SpaceCenterFacility.AstronautComplex);
            var size = gv.GetCraftSizeLimit(pad, true);
            var limits = new Obj
            {
                ["vabPartCount"] = gv.GetPartCountLimit(vab, true),
                ["padMass"] = gv.GetCraftMassLimit(pad, true),
                ["padSize"] = new List<object> { size.x, size.y, size.z },
                ["activeContracts"] = gv.GetActiveContractsLimit(mc),
                ["maneuverNodes"] = gv.UnlockedFlightPlanning(mc),
                ["patchedConics"] = gv.GetOrbitDisplayMode(ts).ToString(),
                ["eva"] = gv.UnlockedEVA(ac),
                ["activeCrew"] = gv.GetActiveCrewLimit(ac),
                ["scienceCostLimit"] = gv.GetScienceCostLimit(Lvl(SpaceCenterFacility.ResearchAndDevelopment)),
                ["actionGroups"] = gv.UnlockedActionGroupsStock(vab, true),
            };
            return Json.Write(new Obj { ["facilities"] = facs, ["limits"] = limits });
        }

        /// <summary>Upgrade a facility one level, paying funds. Space center scene only.</summary>
        [KRPCProcedure]
        public static string UpgradeFacility(string id)
        {
            if (HighLogic.LoadedScene != GameScenes.SPACECENTER)
                throw new InvalidOperationException("go to the space center first");
            if (!id.Contains("/")) id = "SpaceCenter/" + id;
            if (!ScenarioUpgradeableFacilities.protoUpgradeables.TryGetValue(id, out var proto))
                throw new ArgumentException("unknown facility " + id);
            var fac = proto.facilityRefs.FirstOrDefault() ?? throw new InvalidOperationException("facility not loaded");
            if (fac.FacilityLevel >= fac.MaxLevel) throw new InvalidOperationException("already max level");
            var cost = fac.GetUpgradeCost();
            if (Funding.Instance.Funds < cost) throw new InvalidOperationException($"not enough funds ({Funding.Instance.Funds:F0} < {cost:F0})");
            Funding.Instance.AddFunds(-cost, TransactionReasons.StructureConstruction);
            fac.SetLevel(fac.FacilityLevel + 1);
            GamePersistence.SaveGame("persistent", HighLogic.SaveFolder, SaveMode.OVERWRITE);
            return Json.Write(new Obj { ["id"] = id, ["level"] = fac.FacilityLevel + 1, ["funds"] = Funding.Instance.Funds });
        }

        // ---------------- Vessels ----------------

        /// <summary>From the space center / tracking station: save and switch to flying the named vessel
        /// (like "Fly" in the tracking station). Also re-registers contract waypoints on the way in.</summary>
        [KRPCProcedure]
        public static void FlyVessel(string name)
        {
            if (HighLogic.LoadedSceneIsFlight) throw new InvalidOperationException("already in flight; go to the space center first");
            // same as the tracking station's Fly button: the index is into FlightGlobals.Vessels, which can be
            // ordered differently from flightState.protoVessels (that index once focused an asteroid)
            var v = FlightGlobals.Vessels.Find(x => x.vesselName == name);
            if (v == null) throw new ArgumentException("no vessel named " + name);
            GamePersistence.SaveGame("persistent", HighLogic.SaveFolder, SaveMode.OVERWRITE);
            FlightDriver.StartAndFocusVessel("persistent", FlightGlobals.Vessels.IndexOf(v));
        }

        /// <summary>From the space center: save, go to the main menu and load another save folder
        /// (e.g. career <-> sandbox) without restarting KSP.</summary>
        [KRPCProcedure]
        public static void LoadSave(string name)
        {
            if (HighLogic.LoadedSceneIsFlight) throw new InvalidOperationException("go to the space center first");
            if (!System.IO.File.Exists(KSPUtil.ApplicationRootPath + "saves/" + name.Split(':')[0] + "/persistent.sfs"))
                throw new ArgumentException("no save " + name);
            GamePersistence.SaveGame("persistent", HighLogic.SaveFolder, SaveMode.OVERWRITE);
            AutoLoad.Pending = name;
            HighLogic.LoadScene(GameScenes.MAINMENU);
        }

        /// <summary>Time-warp to UT in any scene (kRPC's warp_to is flight-only; the space center and the
        /// tracking station have no altitude warp limit). Returns at once; poll Status().ut.</summary>
        [KRPCProcedure]
        public static void WarpTo(double ut)
        {
            TimeWarp.fetch.WarpTo(ut);
        }

        // ---------------- Space center UI (for screenshots) ----------------

        /// <summary>Open a space-center building's screen, like clicking it: e.g. "RnDBuilding",
        /// "MissionControlBuilding", "AdministrationFacility", "AstronautComplexFacility", "TrackingStationBuilding".</summary>
        [KRPCProcedure]
        public static void OpenFacility(string typeName)
        {
            var b = UnityEngine.Object.FindObjectsOfType<SpaceCenterBuilding>().FirstOrDefault(x => x.GetType().Name == typeName)
                    ?? throw new ArgumentException("no building " + typeName + "; have: " +
                        string.Join(", ", UnityEngine.Object.FindObjectsOfType<SpaceCenterBuilding>().Select(x => x.GetType().Name)));
            b.EnterBuilding();
        }

        /// <summary>Hide or show the game UI (like F2), for clean screenshots.</summary>
        [KRPCProcedure]
        public static void HideUi(bool hide)
        {
            if (hide) GameEvents.onHideUI.Fire(); else GameEvents.onShowUI.Fire();
        }

        /// <summary>Active UI toggles and buttons: "path|kind|label", to find a tab to press with UiPress.</summary>
        [KRPCProcedure]
        public static IList<string> UiList()
        {
            var o = new List<string>();
            foreach (var t in UnityEngine.Object.FindObjectsOfType<UnityEngine.UI.Selectable>())
            {
                if (!t.isActiveAndEnabled) continue;
                var label = t.GetComponentInChildren<TMPro.TextMeshProUGUI>()?.text ?? "";
                o.Add(Path(t.transform) + "|" + t.GetType().Name + "|" + label);
            }
            return o;
        }

        /// <summary>Press the first active toggle/button whose path or label contains `match`.</summary>
        [KRPCProcedure]
        public static string UiPress(string match)
        {
            foreach (var t in UnityEngine.Object.FindObjectsOfType<UnityEngine.UI.Selectable>())
            {
                if (!t.isActiveAndEnabled) continue;
                var label = t.GetComponentInChildren<TMPro.TextMeshProUGUI>()?.text ?? "";
                var path = Path(t.transform);
                if (!path.Contains(match) && !label.Contains(match)) continue;
                if (t is UnityEngine.UI.Toggle tg) tg.isOn = true;
                else if (t is UnityEngine.UI.Button bt) bt.onClick.Invoke();
                else continue;
                return path + "|" + label;
            }
            throw new ArgumentException("no active toggle/button matching " + match);
        }

        static string Path(Transform t) => t.parent == null ? t.name : Path(t.parent) + "/" + t.name;

        // ---------------- Crew ----------------

        /// <summary>Move a kerbal to a free seat in the part named `toPart` (internal name, e.g. mk1pod.v2) on the
        /// active vessel. kRPC's TransferCrew finds the source through crew.seat, which is null for a kerbal that
        /// arrived with a grabbed vessel (Gwenbro after the Klaw grab): NRE. This goes by the parts' crew lists.</summary>
        [KRPCProcedure]
        public static string MoveCrew(string kerbal, string toPart)
        {
            var v = FlightGlobals.ActiveVessel;
            var from = v.parts.FirstOrDefault(p => p.protoModuleCrew.Any(c => c.name == kerbal))
                       ?? throw new ArgumentException(kerbal + " is not aboard");
            var pcm = from.protoModuleCrew.First(c => c.name == kerbal);
            var to = v.parts.FirstOrDefault(p => p != from && p.partInfo.name == toPart && p.CrewCapacity > p.protoModuleCrew.Count)
                     ?? throw new ArgumentException("no free seat in a " + toPart);
            from.RemoveCrewmember(pcm);
            to.AddCrewmember(pcm);
            v.CrewListSetDirty();
            try { v.SpawnCrew(); } catch (Exception) { }
            GameEvents.onCrewTransferred.Fire(new GameEvents.HostedFromToAction<ProtoCrewMember, Part>(pcm, from, to));
            GameEvents.onVesselCrewWasModified.Fire(v);
            return $"{kerbal}: {from.partInfo.title} -> {to.partInfo.title}";
        }

        /// <summary>Hire an applicant from the astronaut complex, paying the hire cost.</summary>
        [KRPCProcedure]
        public static string HireKerbal()
        {
            var roster = HighLogic.CurrentGame.CrewRoster;
            var active = roster.GetActiveCrewCount();
            var ac = Lvl(SpaceCenterFacility.AstronautComplex);
            if (active >= GameVariables.Instance.GetActiveCrewLimit(ac)) throw new InvalidOperationException("crew limit reached");
            var cost = GameVariables.Instance.GetRecruitHireCost(active);
            if (Funding.Instance != null && Funding.Instance.Funds < cost) throw new InvalidOperationException("not enough funds");
            var applicant = roster.Applicants.FirstOrDefault()
                            ?? (HighLogic.CurrentGame.Mode == Game.Modes.SANDBOX  // sandbox tests strand crews on test craft
                                ? roster.GetNewKerbal(ProtoCrewMember.KerbalType.Applicant)
                                : throw new InvalidOperationException("no applicants"));
            Funding.Instance?.AddFunds(-cost, TransactionReasons.CrewRecruited);
            roster.HireApplicant(applicant);
            return Json.Write(new Obj { ["hired"] = applicant.name, ["trait"] = applicant.trait, ["cost"] = cost });
        }

        /// <summary>SANDBOX ONLY: take a kerbal off whatever unloaded vessel holds it (or clear a stale
        /// "Assigned" status) and make it available at the astronaut complex.</summary>
        [KRPCProcedure]
        public static string SandboxReleaseCrew(string name)
        {
            if (HighLogic.CurrentGame.Mode != Game.Modes.SANDBOX) throw new InvalidOperationException("sandbox saves only");
            if (HighLogic.LoadedSceneIsFlight) throw new InvalidOperationException("from the space center");
            var pcm = HighLogic.CurrentGame.CrewRoster[name] ?? throw new ArgumentException("no kerbal " + name);
            var from = "none";
            foreach (var pv in HighLogic.CurrentGame.flightState.protoVessels)
                foreach (var pp in pv.protoPartSnapshots)
                    if (pp.protoModuleCrew.Remove(pcm)) { pp.protoCrewNames.Remove(name); from = pv.vesselName; }
            pcm.rosterStatus = ProtoCrewMember.RosterStatus.Available;
            return Json.Write(new Obj { ["kerbal"] = name, ["from"] = from });
        }

        // ---------------- EVA (kRPC has none) ----------------
        // Science on EVA (EVA report, surface sample) runs through kRPC's experiments on the EVA kerbal vessel.

        static readonly System.Reflection.BindingFlags Any =
            System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic;

        static KerbalEVA ActiveKerbal()
        {
            var v = FlightGlobals.ActiveVessel;
            var k = v != null && v.isEVA ? v.GetComponentInChildren<KerbalEVA>() : null;
            return k ?? throw new InvalidOperationException("active vessel is not an EVA kerbal");
        }

        /// Hatch geometry of the first crewed part with an airlock: position in the part frame (builder angle/height)
        /// and the other parts' colliders within `radius` of it. Minmus Lab 1 (2026-09-26): a kerbal spawned out of
        /// the MPL on the pad kicked the 87 t stack to 1 m/s and it fell over (twice, crew killed, reverted).
        static Obj HatchCheck(float radius)
        {
            var v = FlightGlobals.ActiveVessel;
            var part = v.parts.FirstOrDefault(p => p.protoModuleCrew.Count > 0 && p.airlock != null)
                       ?? throw new InvalidOperationException("no crewed part with a hatch");
            var local = part.transform.InverseTransformPoint(part.airlock.position);
            var hits = new List<object>();
            foreach (var c in Physics.OverlapSphere(part.airlock.position, radius))
            {
                var hp = c.GetComponentInParent<Part>();
                if (hp == null || hp == part) continue;
                float d = -1;
                try { d = Vector3.Distance(c.ClosestPoint(part.airlock.position), part.airlock.position); } catch (Exception) { }
                hits.Add(new Obj { ["part"] = hp.partInfo.name, ["collider"] = c.name, ["trigger"] = c.isTrigger, ["distance"] = d });
            }
            return new Obj { ["part"] = part.partInfo.name, ["airlock"] = part.airlock.name,
                             ["x"] = local.x, ["y"] = local.y, ["z"] = local.z,
                             ["angle"] = Mathf.Atan2(local.z, local.x) * Mathf.Rad2Deg,
                             ["overlaps"] = hits };
        }

        /// <summary>Hatch geometry and colliders of other parts within `radius` m of the airlock (see HatchCheck).</summary>
        [KRPCProcedure]
        public static string EvaCheck(float radius) => Json.Write(HatchCheck(radius));

        /// <summary>Send the first crew member of the active vessel out of its hatch. The kerbal becomes the active vessel.</summary>
        [KRPCProcedure]
        public static string EvaSpawn()
        {
            if (!GameVariables.Instance.UnlockedEVA(ScenarioUpgradeableFacilities.GetFacilityLevel(SpaceCenterFacility.AstronautComplex)))
                throw new InvalidOperationException("EVA not unlocked (Astronaut Complex)");
            var v = FlightGlobals.ActiveVessel;
            var part = v.parts.FirstOrDefault(p => p.protoModuleCrew.Count > 0 && p.airlock != null)
                       ?? throw new InvalidOperationException("no crewed part with a hatch");
            var check = HatchCheck(0.75f);
            if (((List<object>)check["overlaps"]).Count > 0)
                throw new InvalidOperationException("parts overlap the hatch: " + Json.Write(check));
            var crew = part.protoModuleCrew[0];
            var k = FlightEVA.fetch.spawnEVA(crew, part, part.airlock, true)
                    ?? throw new InvalidOperationException("EVA failed (hatch obstructed?)");
            return Json.Write(new Obj { ["kerbal"] = crew.name, ["from"] = part.partInfo.title });
        }

        /// <summary>State of the active EVA kerbal: FSM state, ground contact, the hatch it can board (if any), flags left.</summary>
        [KRPCProcedure]
        public static string EvaState()
        {
            var k = ActiveKerbal();
            var airlock = typeof(KerbalEVA).GetField("currentAirlockPart", Any)?.GetValue(k) as Part;
            return Json.Write(new Obj
            {
                ["state"] = k.fsm.currentStateName,
                ["ground"] = k.part.GroundContact,
                ["situation"] = k.vessel.situation.ToString(),
                ["airlock"] = airlock != null ? airlock.partInfo.title : null,
                ["flags"] = k.flagItems,
            });
        }

        /// A kerbal hanging at the bottom end of a pod's short ladder ("Ladder (End Reached)") is ~0.5 m below
        /// the airlock trigger; a player would climb up a step and board. Accept a crewable part whose airlock
        /// is within `range` metres.
        static Part NearHatch(KerbalEVA k, float range)
        {
            Part best = null;
            var bestD = range;
            foreach (var v in FlightGlobals.VesselsLoaded)
            {
                if (v == k.vessel) continue;
                foreach (var p in v.parts)
                {
                    if (p.airlock == null || p.CrewCapacity <= p.protoModuleCrew.Count) continue;
                    var d = Vector3.Distance(p.airlock.position, k.transform.position);
                    if (d < bestD) { best = p; bestD = d; }
                }
            }
            return best;
        }

        /// <summary>Let go of the ladder (like pressing the ladder-release key): the kerbal drops to the ground.</summary>
        [KRPCProcedure]
        public static string EvaLetGo()
        {
            var k = ActiveKerbal();
            k.fsm.RunEvent(k.On_ladderLetGo);
            return k.fsm.currentStateName;
        }

        /// <summary>Plant a flag (kerbal must stand on the ground).</summary>
        [KRPCProcedure]
        public static void EvaPlantFlag()
        {
            var k = ActiveKerbal();
            var can = (bool)typeof(KerbalEVA).GetMethod("CanPlantFlag", Any).Invoke(k, null);
            if (!can) throw new InvalidOperationException("cannot plant a flag now (not on the ground, no flags, or locked)");
            k.PlantFlag();
        }

        /// <summary>Board the hatch the kerbal is at (same rule as the in-game Board action: must be in the hatch's trigger).</summary>
        [KRPCProcedure]
        public static void EvaBoard()
        {
            var k = ActiveKerbal();
            var airlock = typeof(KerbalEVA).GetField("currentAirlockPart", Any)?.GetValue(k) as Part
                          ?? NearHatch(k, 2.0f)
                          ?? throw new InvalidOperationException("not at a hatch");
            k.BoardPart(airlock);
        }

        // ---------------- Science lab (docs/lab/README.md) ----------------

        static ModuleScienceLab ActiveLab() =>
            FlightGlobals.ActiveVessel?.FindPartModuleImplementing<ModuleScienceLab>()
            ?? throw new InvalidOperationException("no science lab on the active vessel");

        /// Same formula as ExperimentResultDialogPage.UpdatePageLabValue (labValue stays 0 unless the dialog sets it).
        static float LabValue(ModuleScienceLab lab, ScienceData d)
        {
            var v = FlightGlobals.ActiveVessel;
            var s = ResearchAndDevelopment.GetSubjectByID(d.subjectID);
            if (s == null) return 0f;
            float x = ResearchAndDevelopment.GetReferenceDataValue(d.dataAmount, s)
                      * HighLogic.CurrentGame.Parameters.Career.ScienceGainMultiplier;
            if (v.Landed) x *= 1f + lab.SurfaceBonus;
            if (d.subjectID.Contains(FlightGlobals.currentMainBody.bodyName)) x *= 1f + lab.ContextBonus;
            if ((v.Landed || v.Splashed) && v.mainBody == FlightGlobals.GetHomeBody()) x *= lab.homeworldMultiplier;
            return (float)Math.Round(x);
        }

        /// <summary>Lab state: data stored/capacity, science stored/cap, running, scientists, rate, processed subjects.</summary>
        [KRPCProcedure]
        public static string LabStatus()
        {
            var lab = ActiveLab(); var conv = lab.Converter;
            float sci = lab.part.protoModuleCrew.Where(c => c.HasEffect<Experience.Effects.ScienceSkill>())
                           .Sum(c => 1f + conv.scientistBonus * c.experienceLevel);
            double ec = 0, ecMax = 0;
            foreach (var p in lab.vessel.parts)
                foreach (var r in p.Resources)
                    if (r.resourceName == "ElectricCharge") { ec += r.amount; ecMax += r.maxAmount; }
            return Json.Write(new Obj {
                ["dataStored"] = lab.dataStored, ["dataStorage"] = lab.dataStorage,
                ["storedScience"] = lab.storedScience, ["scienceCap"] = conv.scienceCap,
                ["running"] = conv.IsActivated, ["status"] = conv.status, ["scientists"] = sci,
                ["operational"] = lab.IsOperational(), ["sciPerDay"] = conv.CalculateScienceRate(lab.dataStored),
                ["ec"] = ec, ["ecMax"] = ecMax, ["processed"] = lab.ExperimentData.ToList() });
        }

        /// <summary>What the results dialog's lab button does, for every data item on the active vessel.
        /// Data is consumed (non-rerunnable experiments become inoperable; containers lose the item).</summary>
        [KRPCProcedure]
        public static string LabProcess(bool dryRun)
        {
            var v = FlightGlobals.ActiveVessel; var lab = ActiveLab();
            if (!lab.IsOperational()) throw new InvalidOperationException("no scientist in the lab part");
            var rows = new List<object>(); float room = lab.dataStorage - lab.dataStored;
            var seen = new HashSet<string>(lab.ExperimentData);
            foreach (var p in v.parts.ToList())
            foreach (var c in p.Modules.OfType<IScienceDataContainer>().ToList())
            {
                if (c is ModuleScienceLab) continue;
                foreach (var d in c.GetData())
                {
                    d.labValue = LabValue(lab, d);
                    string why = d.labValue <= 0 ? "no value"
                        : seen.Contains(d.subjectID) ? "already processed"
                        : d.labValue > room ? "lab full" : null;
                    if (why == null)
                    {
                        room -= d.labValue; seen.Add(d.subjectID);
                        if (!dryRun)
                        {
                            var it = lab.ProcessData(d); while (it.MoveNext()) { }  // no real yields: stores synchronously
                            if (!lab.ExperimentData.Contains(d.subjectID)) why = "rejected";
                            else if (c is ModuleScienceExperiment e) e.DumpData(d);
                            else if (c is ModuleScienceContainer k) k.RemoveData(d);
                        }
                    }
                    rows.Add(new Obj { ["subject"] = d.subjectID, ["part"] = p.partInfo.name,
                                       ["labValue"] = d.labValue, ["result"] = why ?? (dryRun ? "would process" : "processed") });
                }
            }
            return Json.Write(new Obj { ["items"] = rows, ["dataStored"] = lab.dataStored });
        }

        /// <summary>start | stop research, transmit stored science, clean (reset) the vessel's used experiments.</summary>
        [KRPCProcedure]
        public static string LabAction(string action)
        {
            var lab = ActiveLab();
            switch (action)
            {
                case "start": lab.Converter.StartResourceConverter(); break;
                case "stop": lab.Converter.StopResourceConverter(); break;
                case "transmit": lab.TransmitScience(); break;
                case "clean": lab.CleanModulesEvent(); break;
                default: throw new ArgumentException("start | stop | transmit | clean");
            }
            return LabStatus();
        }

        // ---------------- Craft building ----------------

        /// <summary>
        /// Build a .craft file in the current save's Ships/VAB from a JSON spec (see CraftBuilder).
        /// Returns a JSON summary (path, parts, cost, mass).
        /// </summary>
        [KRPCProcedure]
        public static string BuildCraft(string specJson)
        {
            return CraftBuilder.Build(specJson);
        }
    }
}
