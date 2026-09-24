using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace KspBot
{
    /// Minimal JSON writer. Values: null, bool, numbers, string, IDictionary<string, object>, IEnumerable.
    public static class Json
    {
        public static string Write(object v)
        {
            var sb = new StringBuilder();
            WriteValue(sb, v);
            return sb.ToString();
        }

        static void WriteValue(StringBuilder sb, object v)
        {
            switch (v)
            {
                case null: sb.Append("null"); break;
                case bool b: sb.Append(b ? "true" : "false"); break;
                case string s: WriteString(sb, s); break;
                case float f: sb.Append(Num(f)); break;
                case double d: sb.Append(Num(d)); break;
                case int i: sb.Append(i.ToString(CultureInfo.InvariantCulture)); break;
                case long l: sb.Append(l.ToString(CultureInfo.InvariantCulture)); break;
                case uint u: sb.Append(u.ToString(CultureInfo.InvariantCulture)); break;
                case IDictionary<string, object> dict:
                    sb.Append('{');
                    var first = true;
                    foreach (var kv in dict)
                    {
                        if (!first) sb.Append(',');
                        first = false;
                        WriteString(sb, kv.Key);
                        sb.Append(':');
                        WriteValue(sb, kv.Value);
                    }
                    sb.Append('}');
                    break;
                case System.Collections.IEnumerable list:
                    sb.Append('[');
                    var f2 = true;
                    foreach (var item in list)
                    {
                        if (!f2) sb.Append(',');
                        f2 = false;
                        WriteValue(sb, item);
                    }
                    sb.Append(']');
                    break;
                default: WriteString(sb, v.ToString()); break;
            }
        }

        static string Num(double d)
        {
            if (double.IsNaN(d) || double.IsInfinity(d)) return "null";
            return System.Math.Round(d, 4).ToString("R", CultureInfo.InvariantCulture);
        }

        static void WriteString(StringBuilder sb, string s)
        {
            sb.Append('"');
            foreach (var c in s)
            {
                switch (c)
                {
                    case '"': sb.Append("\\\""); break;
                    case '\\': sb.Append("\\\\"); break;
                    case '\n': sb.Append("\\n"); break;
                    case '\r': sb.Append("\\r"); break;
                    case '\t': sb.Append("\\t"); break;
                    default:
                        if (c < 0x20) sb.Append("\\u").Append(((int)c).ToString("x4"));
                        else sb.Append(c);
                        break;
                }
            }
            sb.Append('"');
        }
    }

    public class Obj : Dictionary<string, object> { }

    /// Minimal JSON reader: objects -> Dictionary<string, object>, arrays -> List<object>, numbers -> double.
    public class JsonReader
    {
        readonly string s;
        int i;

        JsonReader(string s) { this.s = s; }

        public static object Parse(string s)
        {
            var r = new JsonReader(s);
            var v = r.Value();
            r.Ws();
            if (r.i != s.Length) throw r.Err("trailing characters");
            return v;
        }

        System.FormatException Err(string msg) => new System.FormatException($"JSON: {msg} at {i}");

        void Ws() { while (i < s.Length && char.IsWhiteSpace(s[i])) i++; }

        object Value()
        {
            Ws();
            if (i >= s.Length) throw Err("unexpected end");
            var c = s[i];
            if (c == '{')
            {
                i++;
                var d = new Dictionary<string, object>();
                Ws();
                if (s[i] == '}') { i++; return d; }
                while (true)
                {
                    Ws();
                    var k = Str();
                    Ws();
                    if (s[i++] != ':') throw Err("expected ':'");
                    d[k] = Value();
                    Ws();
                    if (s[i] == ',') { i++; continue; }
                    if (s[i] == '}') { i++; return d; }
                    throw Err("expected ',' or '}'");
                }
            }
            if (c == '[')
            {
                i++;
                var l = new List<object>();
                Ws();
                if (s[i] == ']') { i++; return l; }
                while (true)
                {
                    l.Add(Value());
                    Ws();
                    if (s[i] == ',') { i++; continue; }
                    if (s[i] == ']') { i++; return l; }
                    throw Err("expected ',' or ']'");
                }
            }
            if (c == '"') return Str();
            if (s.Substring(i).StartsWith("true")) { i += 4; return true; }
            if (s.Substring(i).StartsWith("false")) { i += 5; return false; }
            if (s.Substring(i).StartsWith("null")) { i += 4; return null; }
            var start = i;
            while (i < s.Length && "+-0123456789.eE".IndexOf(s[i]) >= 0) i++;
            if (start == i) throw Err("unexpected character");
            return double.Parse(s.Substring(start, i - start), CultureInfo.InvariantCulture);
        }

        string Str()
        {
            if (s[i] != '"') throw Err("expected string");
            i++;
            var sb = new StringBuilder();
            while (s[i] != '"')
            {
                var c = s[i++];
                if (c != '\\') { sb.Append(c); continue; }
                var e = s[i++];
                switch (e)
                {
                    case 'n': sb.Append('\n'); break;
                    case 't': sb.Append('\t'); break;
                    case 'r': sb.Append('\r'); break;
                    case 'b': sb.Append('\b'); break;
                    case 'f': sb.Append('\f'); break;
                    case 'u': sb.Append((char)System.Convert.ToInt32(s.Substring(i, 4), 16)); i += 4; break;
                    default: sb.Append(e); break;
                }
            }
            i++;
            return sb.ToString();
        }
    }
}
