// Sketch for mod/KspBot/Service.cs (inside KspBotService). Not compiled. KSP 1.12.5 semantics.
// ---------------- Science lab ----------------
static ModuleScienceLab ActiveLab() =>
    FlightGlobals.ActiveVessel?.FindPartModuleImplementing<ModuleScienceLab>()
    ?? throw new InvalidOperationException("no science lab on the active vessel");

// Same formula as ExperimentResultDialogPage.UpdatePageLabValue (labValue is 0 unless the dialog set it).
static float LabValue(ModuleScienceLab lab, ScienceData d)
{
    var v = FlightGlobals.ActiveVessel;
    var s = ResearchAndDevelopment.GetSubjectByID(d.subjectID);
    if (s == null) return 0f;
    float x = ResearchAndDevelopment.GetReferenceDataValue(d.dataAmount, s)          // dataAmount/dataScale*subjectValue
              * HighLogic.CurrentGame.Parameters.Career.ScienceGainMultiplier;
    if (v.Landed) x *= 1f + lab.SurfaceBonus;                                         // +10 %
    if (d.subjectID.Contains(FlightGlobals.currentMainBody.bodyName)) x *= 1f + lab.ContextBonus; // +25 %
    if ((v.Landed || v.Splashed) && v.mainBody == FlightGlobals.GetHomeBody()) x *= lab.homeworldMultiplier; // x0.1
    return (float)Math.Round(x);
}

[KRPCProcedure]
public static string LabStatus()
{
    var lab = ActiveLab(); var conv = lab.Converter;
    float sci = lab.part.protoModuleCrew.Where(c => c.HasEffect<Experience.Effects.ScienceSkill>())
                   .Sum(c => 1f + conv.scientistBonus * c.experienceLevel);
    return Json.Write(new Obj {
        ["dataStored"] = lab.dataStored, ["dataStorage"] = lab.dataStorage,
        ["storedScience"] = lab.storedScience, ["scienceCap"] = conv.scienceCap,
        ["running"] = conv.IsActivated, ["status"] = conv.status, ["scientists"] = sci,
        ["sciPerDay"] = conv.CalculateScienceRate(lab.dataStored),
        ["processed"] = lab.ExperimentData.ToList() });
}

/// What the results dialog's lab button does, for every data item on the active vessel.
/// Data is consumed (experiments dumped/reset, non-rerunnable -> Inoperable; containers lose the item).
[KRPCProcedure]
public static string LabProcess(bool dryRun)
{
    var v = FlightGlobals.ActiveVessel; var lab = ActiveLab();
    if (!lab.IsOperational()) throw new InvalidOperationException("no scientist in the lab part");
    var rows = new List<object>(); float room = lab.dataStorage - lab.dataStored;
    foreach (var p in v.parts.ToList())
    foreach (var c in p.Modules.OfType<IScienceDataContainer>().ToList())
    {
        if (c is ModuleScienceLab) continue;
        foreach (var d in c.GetData())
        {
            d.labValue = LabValue(lab, d);
            string why = d.labValue <= 0 ? "no value"
                : lab.ExperimentData.Contains(d.subjectID) ? "already processed"
                : d.labValue > room ? "lab full" : null;
            if (why == null) {
                room -= d.labValue;
                if (!dryRun) {
                    var it = lab.ProcessData(d); while (it.MoveNext()) { }   // no real yields: stores synchronously
                    if (!lab.ExperimentData.Contains(d.subjectID)) why = "rejected";
                    else if (c is ModuleScienceExperiment e) e.DumpData(d);  // == sendDataToLab's SetInoperable+endExperiment
                    else if (c is ModuleScienceContainer k) k.RemoveData(d);
                }
            }
            rows.Add(new Obj { ["subject"] = d.subjectID, ["part"] = p.partInfo.name,
                               ["labValue"] = d.labValue, ["result"] = why ?? (dryRun ? "would process" : "processed") });
        }
    }
    return Json.Write(new Obj { ["items"] = rows, ["dataStored"] = lab.dataStored });
}
