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
            var pvs = HighLogic.CurrentGame.flightState.protoVessels;
            var idx = pvs.FindIndex(pv => pv.vesselName == name);
            if (idx < 0) throw new ArgumentException("no vessel named " + name);
            GamePersistence.SaveGame("persistent", HighLogic.SaveFolder, SaveMode.OVERWRITE);
            FlightDriver.StartAndFocusVessel("persistent", idx);
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

        /// <summary>Send the first crew member of the active vessel out of its hatch. The kerbal becomes the active vessel.</summary>
        [KRPCProcedure]
        public static string EvaSpawn()
        {
            if (!GameVariables.Instance.UnlockedEVA(ScenarioUpgradeableFacilities.GetFacilityLevel(SpaceCenterFacility.AstronautComplex)))
                throw new InvalidOperationException("EVA not unlocked (Astronaut Complex)");
            var v = FlightGlobals.ActiveVessel;
            var part = v.parts.FirstOrDefault(p => p.protoModuleCrew.Count > 0 && p.airlock != null)
                       ?? throw new InvalidOperationException("no crewed part with a hatch");
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
                          ?? throw new InvalidOperationException("not at a hatch");
            k.BoardPart(airlock);
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
