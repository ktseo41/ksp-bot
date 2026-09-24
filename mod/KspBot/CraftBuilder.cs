using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEngine;

namespace KspBot
{
    /// <summary>
    /// JSON craft spec:
    /// { "name": "Probe 1", "parts": [
    ///   { "id": "pod", "part": "mk1pod.v2" },                                   // first part = root
    ///   { "id": "chute", "part": "parachuteSingle", "parent": "pod", "node": "top", "stage": 3 },
    ///   { "id": "tank", "part": "fuelTankSmallFlat", "parent": "pod", "node": "bottom" },
    ///   { "id": "fin", "part": "basicFin", "parent": "tank", "symmetry": 3, "height": -0.2 } ] }
    /// node: parent's stack node to attach to (child uses the opposite node unless childNode is set).
    /// No node: surface attach at "height" (parent-local y), "angle" (deg), optional "radius" override.
    /// stage: 1 = fires on first activation (launch), 2 = next, ... 0/absent = no stage.
    /// </summary>
    public class CraftSpec
    {
        public string name;
        public string description;
        public PartSpec[] parts;

        public static CraftSpec FromJson(string json)
        {
            if (!(JsonReader.Parse(json) is Dictionary<string, object> d)) throw new ArgumentException("spec must be an object");
            var spec = new CraftSpec { name = Get<string>(d, "name"), description = Get<string>(d, "description") };
            if (d.TryGetValue("parts", out var p) && p is List<object> list)
                spec.parts = list.Select(x => PartSpec.From((Dictionary<string, object>)x)).ToArray();
            return spec;
        }

        internal static T Get<T>(Dictionary<string, object> d, string k)
        {
            if (!d.TryGetValue(k, out var v) || v == null) return default;
            if (typeof(T) == typeof(string)) return (T)(object)v.ToString();
            return (T)Convert.ChangeType(v, typeof(T));
        }
    }

    public class PartSpec
    {
        public string id;
        public string part;
        public string parent;
        public string node;
        public string childNode;
        public int stage;
        public int symmetry;
        public float height;
        public float angle;
        public float radius;
        public string autostrut;  // Off (default) / Root / Heaviest / Grandparent
        public bool rigid;        // rigid attachment

        public static PartSpec From(Dictionary<string, object> d)
        {
            var known = new[] { "id", "part", "parent", "node", "childNode", "stage", "symmetry", "height", "angle", "radius", "autostrut", "rigid" };
            var bad = d.Keys.Where(k => !known.Contains(k)).ToList();
            if (bad.Count > 0) throw new ArgumentException("unknown part spec keys: " + string.Join(", ", bad));
            return new PartSpec
            {
                id = CraftSpec.Get<string>(d, "id"), part = CraftSpec.Get<string>(d, "part"),
                parent = CraftSpec.Get<string>(d, "parent"), node = CraftSpec.Get<string>(d, "node"),
                childNode = CraftSpec.Get<string>(d, "childNode"), stage = CraftSpec.Get<int>(d, "stage"),
                symmetry = CraftSpec.Get<int>(d, "symmetry"), height = CraftSpec.Get<float>(d, "height"),
                angle = CraftSpec.Get<float>(d, "angle"), radius = CraftSpec.Get<float>(d, "radius"),
                autostrut = CraftSpec.Get<string>(d, "autostrut") ?? "Off", rigid = CraftSpec.Get<bool>(d, "rigid"),
            };
        }
    }

    public static class CraftBuilder
    {
        class Inst
        {
            public PartSpec spec;
            public AvailablePart ap;
            public uint craftId;
            public Vector3 pos;
            public Quaternion rot = Quaternion.identity;
            public Inst parent;
            public string myNode;      // my stack node attached to parent (null if surface / root)
            public string parentNode;  // parent's stack node I am attached to
            public bool surface;
            public readonly List<Inst> children = new List<Inst>();
            public List<Inst> symSet;
            public int istg = -1, sepI = -1, sidx = -1;
            public string Ref => ap.name + "_" + craftId;
        }

        static bool Empty(string s) => string.IsNullOrEmpty(s);

        public static string Build(string specJson)
        {
            var spec = CraftSpec.FromJson(specJson);
            if (spec == null || Empty(spec.name) || spec.parts == null || spec.parts.Length == 0)
                throw new ArgumentException("spec needs name and parts");
            if (spec.name.IndexOfAny(Path.GetInvalidFileNameChars()) >= 0)
                throw new ArgumentException("invalid craft name");

            var byId = new Dictionary<string, List<Inst>>();
            var all = new List<Inst>();
            var warnings = new List<object>();
            uint nextId = 4290000000;

            foreach (var ps in spec.parts)
            {
                if (Empty(ps.id)) ps.id = ps.part;
                if (byId.ContainsKey(ps.id)) throw new ArgumentException("duplicate id " + ps.id);
                var ap = PartLoader.getPartInfoByName(ps.part?.Replace('_', '.'))
                         ?? throw new ArgumentException("unknown part " + ps.part);
                if (!KspBotService.PartUsable(ap)) throw new ArgumentException("part not researched: " + ps.part);
                var made = new List<Inst>();
                if (all.Count == 0)
                {
                    if (!Empty(ps.parent)) throw new ArgumentException("first part must be the root (no parent)");
                    made.Add(new Inst { spec = ps, ap = ap, craftId = nextId++, pos = new Vector3(0, 15, 0) });
                }
                else
                {
                    if (Empty(ps.parent) || !byId.TryGetValue(ps.parent, out var parents))
                        throw new ArgumentException($"{ps.id}: parent '{ps.parent}' must be an earlier part id");
                    foreach (var p in parents)
                    {
                        if (!Empty(ps.node)) made.Add(StackAttach(ps, ap, p, ref nextId));
                        else made.AddRange(SurfaceAttach(ps, ap, p, ref nextId));
                    }
                }
                foreach (var m in made) { m.symSet = made; m.parent?.children.Add(m); }
                byId[ps.id] = made;
                all.AddRange(made);
                if (ps.stage > 0 && !Stageable(ap))
                    warnings.Add($"{ps.id}: {ps.part} has no staging action; stage ignored");
            }

            AssignStages(all);
            var node = Serialize(spec, all);
            var dir = KSPUtil.ApplicationRootPath + "saves/" + HighLogic.SaveFolder + "/Ships/VAB/";
            Directory.CreateDirectory(dir);
            var path = dir + spec.name + ".craft";
            node.Save(path);

            float cost = 0, mass = 0;
            foreach (var i in all)
            {
                cost += i.ap.cost;
                mass += i.ap.partPrefab.mass;
                foreach (var r in i.ap.partPrefab.Resources) mass += (float)(r.amount * r.info.density);
            }
            return Json.Write(new Obj
            {
                ["path"] = path,
                ["name"] = spec.name,
                ["partCount"] = all.Count,
                ["cost"] = cost,
                ["wetMass"] = mass,
                ["stages"] = all.Where(i => i.spec.stage > 0 && Stageable(i.ap)).Max(i => (int?)i.spec.stage) ?? 0,
                ["warnings"] = warnings,
            });
        }

        static bool Stageable(AvailablePart ap)
        {
            var p = ap.partPrefab;
            return p.FindModuleImplementing<ModuleEngines>() != null
                   || p.FindModuleImplementing<ModuleDecouplerBase>() != null
                   || p.FindModuleImplementing<ModuleParachute>() != null
                   || p.FindModuleImplementing<LaunchClamp>() != null
                   || p.FindModuleImplementing<ModuleProceduralFairing>() != null;
        }

        static AttachNode FindNode(AvailablePart ap, string id)
        {
            var n = ap.partPrefab.attachNodes.FirstOrDefault(a => a.id == id);
            if (n == null)
                throw new ArgumentException($"{ap.name} has no node '{id}' (nodes: " +
                                            string.Join(", ", ap.partPrefab.attachNodes.Select(a => a.id)) + ")");
            return n;
        }

        static string Opposite(string node)
        {
            if (node.StartsWith("top")) return "bottom";
            if (node.StartsWith("bottom")) return "top";
            return "bottom";
        }

        static Inst StackAttach(PartSpec ps, AvailablePart ap, Inst p, ref uint nextId)
        {
            var pn = FindNode(p.ap, ps.node);
            var myNodeId = Empty(ps.childNode) ? Opposite(ps.node) : ps.childNode;
            var cn = FindNode(ap, myNodeId);
            if (p.children.Any(c => !c.surface && c.parentNode == pn.id))
                throw new ArgumentException($"{ps.id}: node '{pn.id}' of {p.spec.id} is already used");
            var rot = p.rot;
            var pos = p.pos + p.rot * pn.position - rot * cn.position;
            return new Inst
            {
                spec = ps, ap = ap, craftId = nextId++, pos = pos, rot = rot, parent = p,
                myNode = cn.id, parentNode = pn.id,
            };
        }

        static IEnumerable<Inst> SurfaceAttach(PartSpec ps, AvailablePart ap, Inst p, ref uint nextId)
        {
            var child = ap.partPrefab;
            if (!child.attachRules.srfAttach || child.srfAttachNode == null)
                throw new ArgumentException($"{ps.id}: {ap.name} cannot be surface attached; give a stack node");
            var k = Math.Max(1, ps.symmetry);
            var o = child.srfAttachNode.orientation;
            // angle 0 = parent-local +x, or straight outward when the parent is itself surface-attached
            var baseDir = Vector3.right;
            if (p.surface)
            {
                baseDir = Quaternion.Inverse(Quaternion.LookRotation(p.ap.partPrefab.srfAttachNode.orientation, Vector3.up)) * Vector3.forward;
                baseDir.y = 0;
                baseDir = baseDir.sqrMagnitude > 1e-6f ? baseDir.normalized : Vector3.right;
            }
            var dirs = Enumerable.Range(0, k)
                .Select(j => Quaternion.AngleAxis(ps.angle + 360f * j / k, Vector3.up) * baseDir).ToList();
            // one radius for all symmetry copies: per-direction mesh support differs (Thumper: 1.285 vs 1.372 m),
            // which offset a 3-booster cluster's thrust and tipped Minmus Lander 1 over at liftoff
            var r = ps.radius > 0 ? ps.radius : dirs.Max(d => Support(p.ap, d, ps.height));
            var result = new List<Inst>();
            foreach (var n in dirs)
            {
                var s = new Vector3(0, ps.height, 0) + n * r;
                // same rule as the VAB editor: LookRotation(surface normal) * LookRotation(node orientation)
                var q = Quaternion.LookRotation(n, Vector3.up) * Quaternion.LookRotation(o, Vector3.up);
                var local = s - q * child.srfAttachNode.position;
                result.Add(new Inst
                {
                    spec = ps, ap = ap, craftId = nextId++, pos = p.pos + p.rot * local, rot = p.rot * q,
                    parent = p, surface = true,
                });
            }
            return result;
        }

        /// Distance from the part axis to its visible surface in direction n near height h (part-local).
        static float Support(AvailablePart ap, Vector3 n, float h)
        {
            var root = ap.partPrefab.transform;
            float band = 0, all = 0;
            bool inBand = false;
            foreach (var mf in root.GetComponentsInChildren<MeshFilter>(true))
            {
                if (mf.sharedMesh == null || !ActiveUnder(mf.transform, root)) continue;
                var rend = mf.GetComponent<Renderer>();
                if (rend != null && !rend.enabled) continue;
                Vector3[] verts;
                try { verts = mf.sharedMesh.vertices; } catch { continue; }
                var m = root.worldToLocalMatrix * mf.transform.localToWorldMatrix;
                foreach (var v in verts)
                {
                    var w = m.MultiplyPoint3x4(v);
                    var d = w.x * n.x + w.z * n.z;
                    if (d > all) all = d;
                    if (Mathf.Abs(w.y - h) < 0.15f && d > band) { band = d; inBand = true; }
                }
            }
            if (inBand && band > 0.01f) return band;
            if (all > 0.01f) return all;
            var size = ap.partPrefab.attachNodes.Select(x => x.size).DefaultIfEmpty(1).Max();
            return size == 0 ? 0.3125f : 0.625f * size;
        }

        static bool ActiveUnder(Transform t, Transform root)
        {
            for (; t != null && t != root; t = t.parent)
                if (!t.gameObject.activeSelf) return false;
            return true;
        }

        static void AssignStages(List<Inst> all)
        {
            var staged = all.Where(i => i.spec.stage > 0 && Stageable(i.ap)).ToList();
            var maxStage = staged.Count == 0 ? 0 : staged.Max(i => i.spec.stage);
            foreach (var i in staged) i.istg = maxStage - i.spec.stage;
            foreach (var g in staged.GroupBy(i => i.istg))
            {
                int k = 0;
                foreach (var i in g) i.sidx = k++;
            }
            // non-staged parts inherit; separation index follows the nearest decoupler above
            foreach (var i in all) // parents always precede children
            {
                var isDecoupler = i.ap.partPrefab.FindModuleImplementing<ModuleDecouplerBase>() != null;
                if (i.spec.stage <= 0 || !Stageable(i.ap)) i.istg = i.parent?.istg ?? -1;
                i.sepI = isDecoupler && i.spec.stage > 0 ? i.istg : (i.parent?.sepI ?? -1);
            }
        }

        static ConfigNode Serialize(CraftSpec spec, List<Inst> all)
        {
            var root = new ConfigNode();
            root.AddValue("ship", spec.name);
            root.AddValue("version", "1.12.5");
            root.AddValue("description", spec.description ?? "");
            root.AddValue("type", "VAB");
            root.AddValue("size", "3,10,3");
            root.AddValue("steamPublishedFileId", 0);
            root.AddValue("persistentId", (uint)UnityEngine.Random.Range(1, int.MaxValue));
            root.AddValue("rot", "0,0,0,1");
            root.AddValue("missionFlag", "Squad/Flags/default");
            root.AddValue("vesselType", "Ship");
            foreach (var i in all)
            {
                var n = root.AddNode("PART");
                n.AddValue("part", i.Ref);
                n.AddValue("partName", "Part");
                n.AddValue("persistentId", (uint)UnityEngine.Random.Range(1, int.MaxValue));
                n.AddValue("pos", KSPUtil.WriteVector(i.pos));
                var attPos0 = i.parent == null ? i.pos : Quaternion.Inverse(i.parent.rot) * (i.pos - i.parent.pos);
                var attRot0 = i.parent == null ? i.rot : Quaternion.Inverse(i.parent.rot) * i.rot;
                n.AddValue("attPos", "0,0,0");
                n.AddValue("attPos0", KSPUtil.WriteVector(attPos0));
                n.AddValue("rot", KSPUtil.WriteQuaternion(i.rot));
                n.AddValue("attRot", "0,0,0,1");
                n.AddValue("attRot0", KSPUtil.WriteQuaternion(attRot0));
                n.AddValue("mir", "1,1,1");
                n.AddValue("symMethod", "Radial");
                n.AddValue("autostrutMode", i.spec.autostrut);
                n.AddValue("rigidAttachment", i.spec.rigid ? "True" : "False");
                n.AddValue("istg", i.istg);
                n.AddValue("resPri", 0);
                n.AddValue("dstg", i.istg);
                n.AddValue("sidx", i.sidx);
                n.AddValue("sqor", i.sidx >= 0 ? i.istg : -1);
                n.AddValue("sepI", i.sepI);
                n.AddValue("attm", i.surface ? 1 : 0);
                n.AddValue("sameVesselCollision", "False");
                n.AddValue("modCost", 0);
                n.AddValue("modMass", 0);
                n.AddValue("modSize", "0,0,0");
                foreach (var c in i.children) n.AddValue("link", c.Ref);
                if (i.symSet.Count > 1)
                    foreach (var s in i.symSet.Where(s => s != i)) n.AddValue("sym", s.Ref);
                if (i.surface) n.AddValue("srfN", "srfAttach," + i.parent.Ref);
                if (i.myNode != null)
                    n.AddValue("attN", i.myNode + "," + i.parent.Ref + "_" + NodePos(i.ap, i.myNode));
                foreach (var c in i.children.Where(c => !c.surface))
                    n.AddValue("attN", c.parentNode + "," + c.Ref + "_" + NodePos(i.ap, c.parentNode));
            }
            return root;
        }

        static string NodePos(AvailablePart ap, string nodeId) =>
            KSPUtil.WriteVector(FindNode(ap, nodeId).position, "|");
    }
}
