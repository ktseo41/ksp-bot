using System.Collections;
using System.IO;
using UnityEngine;

namespace KspBot
{
    /// At the main menu, loads (or creates as a Normal career) the save named in
    /// GameData/KspBot/PluginData/autoload.txt, so the game can be driven without clicking.
    [KSPAddon(KSPAddon.Startup.MainMenu, false)]
    public class AutoLoad : MonoBehaviour
    {
        static bool done;

        void Start()
        {
            if (done) return;
            done = true;
            StartCoroutine(Run());
        }

        IEnumerator Run()
        {
            for (int i = 0; i < 30; i++) yield return null;
            var cfg = KSPUtil.ApplicationRootPath + "GameData/KspBot/PluginData/autoload.txt";
            if (!File.Exists(cfg)) yield break;
            // "<save>" or "<save>:sandbox" (new saves only; default is a Normal career)
            var parts = File.ReadAllText(cfg).Trim().Split(':');
            var name = parts[0];
            var mode = parts.Length > 1 && parts[1] == "sandbox" ? Game.Modes.SANDBOX : Game.Modes.CAREER;
            if (name.Length == 0) yield break;
            if (File.Exists(KSPUtil.ApplicationRootPath + "saves/" + name + "/persistent.sfs"))
            {
                Debug.Log("[KspBot] loading save " + name);
                var node = GamePersistence.LoadSFSFile("persistent", name);
                HighLogic.CurrentGame = GamePersistence.LoadGameCfg(node, name, true, false);
                if (HighLogic.CurrentGame == null) { Debug.LogError("[KspBot] incompatible save " + name); yield break; }
                GamePersistence.UpdateScenarioModules(HighLogic.CurrentGame);
                GameEvents.onGameStatePostLoad.Fire(node);
                HighLogic.SaveFolder = name;
                HighLogic.CurrentGame.Start();
            }
            else
            {
                Debug.Log("[KspBot] creating Normal " + mode + " " + name);
                var pars = GameParameters.GetDefaultParameters(mode, GameParameters.Preset.Normal);
                HighLogic.CurrentGame = GamePersistence.CreateNewGame(name, mode, pars,
                    "Squad/Flags/default", GameScenes.SPACECENTER, EditorFacility.None);
                GameEvents.onGameNewStart.Fire();
                HighLogic.CurrentGame.Start();
            }
        }
    }
}
