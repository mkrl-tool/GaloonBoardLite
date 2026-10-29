using System;
using System.Collections;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.IO;
using System.Net;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Text;
using System.Web.Script.Serialization;
using System.Windows.Forms;

[assembly: AssemblyTitle("行動予定表 GaloonBoard Lite")]
[assembly: AssemblyDescription("サイボウズ ガルーン連携 ホワイトボード型 行動予定表 デスクトップアプリ")]
[assembly: AssemblyCompany("Internal Tool")]
[assembly: AssemblyProduct("GaloonBoardLite")]
[assembly: AssemblyCopyright("Copyright (C) 2026")]
[assembly: AssemblyTrademark("")]
[assembly: AssemblyCulture("")]
[assembly: AssemblyVersion("1.0.0.0")]
[assembly: AssemblyFileVersion("1.0.0.0")]

namespace GaloonBoard
{
    public class UserItem
    {
        public string Id { get; set; }
        public string Name { get; set; }
        public string Code { get; set; }

        public UserItem(string id, string name, string code = "")
        {
            Id = id;
            Name = name;
            Code = code;
        }

        public override string ToString()
        {
            if (!string.IsNullOrEmpty(Code))
                return string.Format("{0} ({1})", Name, Code);
            return Name;
        }
    }

    public class ScheduleEvent
    {
        public string TimeRange { get; set; }
        public string Menu { get; set; }
        public string Subject { get; set; }
        public string Notes { get; set; }
        public bool IsAllDay { get; set; }
        public bool IsCurrentActive { get; set; }
        public DateTime StartTime { get; set; }

        public ScheduleEvent(string timeRange, string menu, string subject, string notes = "", bool isAllDay = false, bool isCurrentActive = false)
        {
            TimeRange = timeRange;
            Menu = menu;
            Subject = subject;
            Notes = notes;
            IsAllDay = isAllDay;
            IsCurrentActive = isCurrentActive;
        }
    }

    public class MemberStatus
    {
        public string Name { get; set; }
        public string Destination { get; set; }
        public string ReturnTime { get; set; }
        public Color InkColor { get; set; }
        public string Notes { get; set; }

        public bool IsNenkyu { get; set; } // 年休（赤背景バッジ）
        public bool IsZaitaku { get; set; } // 在宅（黄色背景バッジ）

        // そのユーザーの1日の全スケジュール
        public List<ScheduleEvent> DayEvents { get; set; }

        public MemberStatus(string name, string dest, string retTime, Color color, string notes = "", bool isNenkyu = false, bool isZaitaku = false)
        {
            Name = name;
            Destination = dest;
            ReturnTime = retTime;
            InkColor = color;
            Notes = notes;
            IsNenkyu = isNenkyu;
            IsZaitaku = isZaitaku;
            DayEvents = new List<ScheduleEvent>();
        }
    }

    public class Config
    {
        public string GaroonUrl = "http://garoon.example.local/cgi-bin/cbgrn/grn.cgi";
        public string Username = "";
        public string Password = "";
        public bool UseBasicAuth = false;
        public string BasicUsername = "";
        public string BasicPassword = "";
        public bool VerifySsl = true;
        public int RefreshIntervalMinutes = 20; // 標準20分
        public bool MockMode = true;
        public int WindowWidth = 360;
        public int WindowHeight = 670;
        public int WindowX = -1;
        public int WindowY = -1;
        public bool AlwaysOnTop = false;
        public float FontScale = 1.0f;

        public List<UserItem> AddedUsers = new List<UserItem>();
        public List<string> CheckedUserIds = new List<string>();

        public static string GetConfigPath()
        {
            string dir = AppDomain.CurrentDomain.BaseDirectory;
            return Path.Combine(dir, "board_config.txt");
        }

        public void Save()
        {
            try
            {
                var sb = new StringBuilder();
                sb.AppendLine("MockMode=" + MockMode);
                sb.AppendLine("GaroonUrl=" + GaroonUrl);
                sb.AppendLine("Username=" + Username);
                sb.AppendLine("Password=" + Password);
                sb.AppendLine("UseBasicAuth=" + UseBasicAuth);
                sb.AppendLine("BasicUsername=" + BasicUsername);
                sb.AppendLine("BasicPassword=" + BasicPassword);
                sb.AppendLine("VerifySsl=" + VerifySsl);
                sb.AppendLine("RefreshIntervalMinutes=" + RefreshIntervalMinutes);
                sb.AppendLine("WindowWidth=" + WindowWidth);
                sb.AppendLine("WindowHeight=" + WindowHeight);
                sb.AppendLine("WindowX=" + WindowX);
                sb.AppendLine("WindowY=" + WindowY);
                sb.AppendLine("AlwaysOnTop=" + AlwaysOnTop);
                sb.AppendLine("FontScale=" + FontScale.ToString("0.00", System.Globalization.CultureInfo.InvariantCulture));

                var userStrs = new List<string>();
                foreach (var u in AddedUsers)
                {
                    userStrs.Add(string.Format("{0}|{1}|{2}", u.Id, u.Name, u.Code));
                }
                sb.AppendLine("AddedUsers=" + string.Join(",", userStrs.ToArray()));
                sb.AppendLine("CheckedUserIds=" + string.Join(",", CheckedUserIds.ToArray()));

                File.WriteAllText(GetConfigPath(), sb.ToString(), Encoding.UTF8);
            }
            catch { }
        }

        public static Config Load()
        {
            var cfg = new Config();
            string p = GetConfigPath();
            if (File.Exists(p))
            {
                try
                {
                    foreach (var line in File.ReadAllLines(p, Encoding.UTF8))
                    {
                        var parts = line.Split(new char[] { '=' }, 2);
                        if (parts.Length == 2)
                        {
                            string k = parts[0].Trim();
                            string v = parts[1].Trim();
                            if (k == "MockMode") cfg.MockMode = v.ToLower() == "true";
                            else if (k == "GaroonUrl") cfg.GaroonUrl = v;
                            else if (k == "Username") cfg.Username = v;
                            else if (k == "Password") cfg.Password = v;
                            else if (k == "UseBasicAuth") cfg.UseBasicAuth = v.ToLower() == "true";
                            else if (k == "BasicUsername") cfg.BasicUsername = v;
                            else if (k == "BasicPassword") cfg.BasicPassword = v;
                            else if (k == "VerifySsl") cfg.VerifySsl = v.ToLower() == "true";
                            else if (k == "RefreshIntervalMinutes") int.TryParse(v, out cfg.RefreshIntervalMinutes);
                            else if (k == "WindowWidth") int.TryParse(v, out cfg.WindowWidth);
                            else if (k == "WindowHeight") int.TryParse(v, out cfg.WindowHeight);
                            else if (k == "WindowX") int.TryParse(v, out cfg.WindowX);
                            else if (k == "WindowY") int.TryParse(v, out cfg.WindowY);
                            else if (k == "AlwaysOnTop") cfg.AlwaysOnTop = v.ToLower() == "true";
                            else if (k == "FontScale") float.TryParse(v, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out cfg.FontScale);
                            else if (k == "AddedUsers")
                            {
                                cfg.AddedUsers.Clear();
                                foreach (var item in v.Split(new char[] { ',' }, StringSplitOptions.RemoveEmptyEntries))
                                {
                                    var uParts = item.Split('|');
                                    if (uParts.Length >= 2)
                                    {
                                        string code = uParts.Length > 2 ? uParts[2] : "";
                                        cfg.AddedUsers.Add(new UserItem(uParts[0], uParts[1], code));
                                    }
                                }
                            }
                            else if (k == "CheckedUserIds")
                            {
                                cfg.CheckedUserIds.Clear();
                                foreach (var id in v.Split(new char[] { ',' }, StringSplitOptions.RemoveEmptyEntries))
                                {
                                    string s = id.Trim();
                                    if (!string.IsNullOrEmpty(s)) cfg.CheckedUserIds.Add(s);
                                }
                            }
                        }
                    }
                }
                catch { }
            }

            if (cfg.AddedUsers.Count == 0)
            {
                cfg.AddedUsers.Add(new UserItem("1", "山田 太郎", "yamada"));
                cfg.AddedUsers.Add(new UserItem("2", "佐藤 美咲", "sato"));
                cfg.AddedUsers.Add(new UserItem("3", "鈴木 一郎", "suzuki"));
                cfg.AddedUsers.Add(new UserItem("4", "高橋 健太", "takahashi"));
                cfg.AddedUsers.Add(new UserItem("5", "伊藤 翔太", "ito"));
                cfg.AddedUsers.Add(new UserItem("6", "渡辺 裕子", "watanabe"));

                cfg.CheckedUserIds.Add("1");
                cfg.CheckedUserIds.Add("2");
                cfg.CheckedUserIds.Add("3");
                cfg.CheckedUserIds.Add("4");
                cfg.CheckedUserIds.Add("5");
                cfg.CheckedUserIds.Add("6");
                cfg.Save();
            }

            if (cfg.FontScale < 0.7f || cfg.FontScale > 2.0f) cfg.FontScale = 1.0f;
            return cfg;
        }
    }

    public class WhiteboardForm : Form
    {
        [DllImport("user32.dll")]
        public static extern bool ReleaseCapture();
        [DllImport("user32.dll")]
        public static extern int SendMessage(IntPtr hWnd, int Msg, int wParam, int lParam);
        private const int WM_NCLBUTTONDOWN = 0xA1;
        private const int HT_CAPTION = 0x2;

        private const int WM_NCHITTEST = 0x84;
        private const int HTLEFT = 10;
        private const int HTRIGHT = 11;
        private const int HTTOP = 12;
        private const int HTTOPLEFT = 13;
        private const int HTTOPRIGHT = 14;
        private const int HTBOTTOM = 15;
        private const int HTBOTTOMLEFT = 16;
        private const int HTBOTTOMRIGHT = 17;
        private const int ResizeBorder = 8;

        private Config config;
        private DateTime currentDate;
        private List<MemberStatus> members = new List<MemberStatus>();
        private Timer autoTimer;

        private Rectangle rectPrevDay, rectToday, rectNextDay;
        private Rectangle rectPin, rectRefresh, rectMinus, rectPlus, rectSettings, rectMinimize, rectClose;
        private ToolTip buttonToolTip;
        private string lastToolTipText = "";

        public WhiteboardForm()
        {
            config = Config.Load();
            currentDate = DateTime.Today;

            buttonToolTip = new ToolTip();
            buttonToolTip.InitialDelay = 250;
            buttonToolTip.ReshowDelay = 100;

            this.Text = "行動予定表";
            this.FormBorderStyle = FormBorderStyle.None;
            this.ShowInTaskbar = true;
            this.StartPosition = FormStartPosition.CenterScreen;
            this.ClientSize = new Size(Math.Max(320, config.WindowWidth), Math.Max(500, config.WindowHeight));
            this.MinimumSize = new Size(300, 450);
            this.DoubleBuffered = true;
            this.SetStyle(ControlStyles.ResizeRedraw, true);

            if (config.WindowX >= 0 && config.WindowY >= 0)
            {
                this.Location = new Point(config.WindowX, config.WindowY);
            }
            this.TopMost = config.AlwaysOnTop;

            UpdateFormRegion();
            InitTimer();
            LoadData();
        }

        private void UpdateFormRegion()
        {
            using (var path = GetRoundedRect(new Rectangle(0, 0, this.Width, this.Height), 20))
            {
                this.Region = new Region(path);
            }
        }

        protected override void OnResize(EventArgs e)
        {
            base.OnResize(e);
            UpdateFormRegion();
            this.Invalidate();
        }

        protected override void WndProc(ref Message m)
        {
            if (m.Msg == WM_NCHITTEST)
            {
                base.WndProc(ref m);
                Point p = this.PointToClient(new Point(m.LParam.ToInt32()));

                bool left = p.X <= ResizeBorder;
                bool right = p.X >= this.ClientSize.Width - ResizeBorder;
                bool top = p.Y <= ResizeBorder;
                bool bottom = p.Y >= this.ClientSize.Height - ResizeBorder;

                if (top && left) { m.Result = (IntPtr)HTTOPLEFT; return; }
                if (top && right) { m.Result = (IntPtr)HTTOPRIGHT; return; }
                if (bottom && left) { m.Result = (IntPtr)HTBOTTOMLEFT; return; }
                if (bottom && right) { m.Result = (IntPtr)HTBOTTOMRIGHT; return; }
                if (left) { m.Result = (IntPtr)HTLEFT; return; }
                if (right) { m.Result = (IntPtr)HTRIGHT; return; }
                if (top) { m.Result = (IntPtr)HTTOP; return; }
                if (bottom) { m.Result = (IntPtr)HTBOTTOM; return; }
                return;
            }
            base.WndProc(ref m);
        }

        private void InitTimer()
        {
            autoTimer = new Timer();
            int minutes = config.RefreshIntervalMinutes > 0 ? config.RefreshIntervalMinutes : 20;
            autoTimer.Interval = minutes * 60 * 1000;
            autoTimer.Tick += (s, e) => { LoadData(); };
            autoTimer.Start();
        }

        private void LoadData()
        {
            members.Clear();

            var checkedSet = new HashSet<string>(config.CheckedUserIds);
            var targetUsers = config.AddedUsers.FindAll(u => checkedSet.Contains(u.Id));

            if (targetUsers.Count == 0)
            {
                members.Add(new MemberStatus("案内", "表示するメンバーが選択されていません", "", Color.FromArgb(100, 116, 139), "右上の⚙（設定）からメンバーを追加・チェックしてください。"));
                this.Invalidate();
                return;
            }

            if (config.MockMode)
            {
                LoadMockData(targetUsers);
            }
            else
            {
                FetchGaroonData(targetUsers);
            }
            this.Invalidate();
        }

        private void LoadMockData(List<UserItem> targetUsers)
        {
            DateTime now = DateTime.Now;

            foreach (var u in targetUsers)
            {
                if (u.Id == "1") // 山田 太郎
                {
                    // 10:00〜17:30 の外出予定あり
                    var m = new MemberStatus(u.Name, "外出 株式会社ABC様", "17:30", Color.FromArgb(220, 38, 38), "新システム導入進捗報告");
                    m.DayEvents.Add(new ScheduleEvent("10:00 - 12:30", "外出", "株式会社ABC様 定例打ち合わせ", "新システム導入進捗報告 / 本社3F会議室", false, true));
                    m.DayEvents.Add(new ScheduleEvent("14:00 - 15:30", "会議", "営業部 課会", "第2会議室"));
                    m.DayEvents.Add(new ScheduleEvent("17:00 - 18:00", "", "夕方案件整理・日報", "自席"));
                    members.Add(m);
                }
                else if (u.Id == "2") // 佐藤 美咲: 在宅
                {
                    var m = new MemberStatus(u.Name, "在宅", "終日", Color.FromArgb(24, 24, 27), "Teamsにて連絡可", false, true);
                    m.DayEvents.Add(new ScheduleEvent("終日", "在宅", "終日在宅勤務", "Teamsにて連絡可", true, true));
                    m.DayEvents.Add(new ScheduleEvent("10:00 - 11:30", "会議", "ABC様 定例打ち合わせ (Web参加)", "Teams会議"));
                    m.DayEvents.Add(new ScheduleEvent("16:00 - 16:45", "面談", "1on1 ミーティング", "Zoomにて"));
                    members.Add(m);
                }
                else if (u.Id == "3") // 鈴木 一郎: スケジュールの予定なし -> 確実に「在席」
                {
                    var m = new MemberStatus(u.Name, "在席", "―", Color.FromArgb(24, 24, 27));
                    m.DayEvents.Add(new ScheduleEvent("09:30 - 11:30", "業務", "仕様書作成・設計レビュー準備", "自席にて作業"));
                    members.Add(m);
                }
                else if (u.Id == "4") // 高橋 健太: 年休
                {
                    var m = new MemberStatus(u.Name, "年休", "終日", Color.FromArgb(24, 24, 27), "私用のため終日不在", true, false);
                    m.DayEvents.Add(new ScheduleEvent("終日", "年休", "有給休暇（私用）", "終日不在 / 緊急時はメールへ", true, true));
                    members.Add(m);
                }
                else if (u.Id == "5") // 伊藤 翔太: 外出直帰
                {
                    var m = new MemberStatus(u.Name, "品川DC保守 (直帰)", "直帰", Color.FromArgb(220, 38, 38), "完了後そのまま直帰");
                    m.DayEvents.Add(new ScheduleEvent("10:30 - 11:30", "研修", "社内セキュリティ教育", "大会議室"));
                    m.DayEvents.Add(new ScheduleEvent("14:30 - 18:00", "外出", "品川DC保守立ち会い (直帰)", "完了後そのまま直帰", false, true));
                    members.Add(m);
                }
                else if (u.Id == "6") // 渡辺 裕子: 在宅 ＋ 面談
                {
                    var m = new MemberStatus(u.Name, "採用面接 (Web)", "12:00", Color.FromArgb(37, 99, 235), "Web応接室", false, true);
                    m.DayEvents.Add(new ScheduleEvent("終日", "在宅", "在宅勤務", "リモートワーク", true));
                    m.DayEvents.Add(new ScheduleEvent("11:00 - 12:00", "面談", "採用面接 (Web)", "Web応接室", false, true));
                    m.DayEvents.Add(new ScheduleEvent("15:00 - 16:30", "会議", "全社月次報告会", "オンライン配信"));
                    members.Add(m);
                }
                else
                {
                    // 予定なしの人 -> 確実に「在席」
                    var m = new MemberStatus(u.Name, "在席", "―", Color.FromArgb(24, 24, 27));
                    members.Add(m);
                }
            }
        }

        private void FetchGaroonData(List<UserItem> targetUsers)
        {
            try
            {
                if (!config.VerifySsl)
                {
                    ServicePointManager.ServerCertificateValidationCallback = delegate { return true; };
                }
                ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls12;

                string baseUrl = config.GaroonUrl.TrimEnd('/');
                if (!baseUrl.EndsWith("/api/v1"))
                {
                    if (baseUrl.Contains("grn.cgi") || baseUrl.Contains("grn.exe"))
                        baseUrl += "/api/v1";
                    else
                        baseUrl += "/api/v1";
                }

                DateTime now = DateTime.Now;
                string dateStr = currentDate.ToString("yyyy-MM-dd");
                string rangeStart = dateStr + "T00:00:00+09:00";
                string rangeEnd = dateStr + "T23:59:59+09:00";

                var serializer = new JavaScriptSerializer();

                foreach (var user in targetUsers)
                {
                    string evUrl = string.Format("{0}/schedule/events?rangeStart={1}&rangeEnd={2}&targetType=user&target={3}&limit=100",
                        baseUrl, rangeStart, rangeEnd, user.Id);

                    var req = (HttpWebRequest)WebRequest.Create(evUrl);
                    req.Timeout = 10000;
                    ApplyAuthHeaders(req);

                    string destText = "在席";
                    string returnTimeText = "―";
                    Color inkColor = Color.FromArgb(24, 24, 27);
                    string notesText = "";
                    bool isNenkyu = false;
                    bool isZaitaku = false;
                    var dayEvents = new List<ScheduleEvent>();

                    using (var resp = req.GetResponse())
                    using (var reader = new StreamReader(resp.GetResponseStream(), Encoding.UTF8))
                    {
                        string json = reader.ReadToEnd();
                        var data = serializer.Deserialize<Dictionary<string, object>>(json);
                        if (data != null && data.ContainsKey("events"))
                        {
                            var evList = data["events"] as ArrayList;
                            if (evList != null)
                            {
                                object activeTimedEvent = null;
                                DateTime activeEndTime = DateTime.MinValue;

                                foreach (Dictionary<string, object> ev in evList)
                                {
                                    string subj = ev.ContainsKey("subject") ? (ev["subject"] as string) : "";
                                    string menu = ev.ContainsKey("eventMenu") ? (ev["eventMenu"] as string) : "";
                                    string notes = ev.ContainsKey("notes") ? (ev["notes"] as string) : "";
                                    bool isAllDay = ev.ContainsKey("isAllDay") && Convert.ToBoolean(ev["isAllDay"]);
                                    string fullText = (subj + " " + menu + " " + notes);

                                    // 年休チェック
                                    if (fullText.Contains("年休") || fullText.Contains("有休") || fullText.Contains("有給"))
                                    {
                                        isNenkyu = true;
                                        notesText = notes;
                                    }

                                    // 在宅チェック
                                    if (fullText.Contains("在宅") || fullText.Contains("テレワーク") || fullText.Contains("リモート"))
                                    {
                                        isZaitaku = true;
                                        notesText = notes;
                                    }

                                    // 時間の解析
                                    string timeRangeStr = isAllDay ? "終日" : "";
                                    DateTime startDt = DateTime.MinValue, endDt = DateTime.MinValue;
                                    bool isCurrentlyActive = false;

                                    if (ev.ContainsKey("start") && ev.ContainsKey("end"))
                                    {
                                        var startDict = ev["start"] as Dictionary<string, object>;
                                        var endDict = ev["end"] as Dictionary<string, object>;
                                        if (startDict != null && endDict != null &&
                                            startDict.ContainsKey("dateTime") && endDict.ContainsKey("dateTime"))
                                        {
                                            DateTime.TryParse(startDict["dateTime"].ToString(), out startDt);
                                            DateTime.TryParse(endDict["dateTime"].ToString(), out endDt);
                                            if (startDt != DateTime.MinValue && endDt != DateTime.MinValue)
                                            {
                                                timeRangeStr = string.Format("{0:HH:mm} - {1:HH:mm}", startDt, endDt);

                                                // 現在時刻と一致しているか
                                                if (currentDate.Date == now.Date && startDt <= now && now <= endDt)
                                                {
                                                    activeTimedEvent = ev;
                                                    activeEndTime = endDt;
                                                    isCurrentlyActive = true;
                                                }
                                            }
                                        }
                                    }

                                    // 1日のスケジュール一覧に追加
                                    var schEv = new ScheduleEvent(timeRangeStr, menu, subj, notes, isAllDay, isCurrentlyActive);
                                    schEv.StartTime = startDt;
                                    dayEvents.Add(schEv);
                                }

                                // 時間指定予定の現在一致がある場合
                                if (activeTimedEvent != null)
                                {
                                    var ev = (Dictionary<string, object>)activeTimedEvent;
                                    string subj = ev.ContainsKey("subject") ? (ev["subject"] as string) : "";
                                    string menu = ev.ContainsKey("eventMenu") ? (ev["eventMenu"] as string) : "";
                                    string notes = ev.ContainsKey("notes") ? (ev["notes"] as string) : "";
                                    notesText = notes;

                                    if (subj.Contains("直帰") || notes.Contains("直帰"))
                                    {
                                        returnTimeText = "直帰";
                                    }
                                    else if (activeEndTime != DateTime.MinValue)
                                    {
                                        returnTimeText = activeEndTime.ToString("HH:mm");
                                    }

                                    if (!string.IsNullOrEmpty(menu) && !string.IsNullOrEmpty(subj) && !subj.Contains(menu))
                                    {
                                        destText = menu + " " + subj;
                                    }
                                    else
                                    {
                                        destText = !string.IsNullOrEmpty(subj) ? subj : menu;
                                    }

                                    if (destText.Contains("外出") || destText.Contains("出張") || destText.Contains("訪問") || destText.Contains("直帰"))
                                        inkColor = Color.FromArgb(220, 38, 38);
                                    else if (destText.Contains("会議") || destText.Contains("打合せ") || destText.Contains("MTG") || destText.Contains("面談"))
                                        inkColor = Color.FromArgb(37, 99, 235);
                                }
                            }
                        }
                    }

                    // 年休 / 在宅 / 在席の最終判定
                    if (isNenkyu)
                    {
                        destText = "年休";
                        returnTimeText = "終日";
                    }
                    else if (isZaitaku && destText == "在席")
                    {
                        destText = "在宅";
                        returnTimeText = "終日";
                    }
                    else if (destText == "在席")
                    {
                        // 予定がない人は確実に「在席」「―」
                        destText = "在席";
                        returnTimeText = "―";
                    }

                    var ms = new MemberStatus(user.Name, destText, returnTimeText, inkColor, notesText, isNenkyu, isZaitaku);
                    ms.DayEvents = dayEvents;
                    members.Add(ms);
                }
            }
            catch (Exception ex)
            {
                members.Add(new MemberStatus("通信エラー", ex.Message.Length > 20 ? ex.Message.Substring(0, 20) : ex.Message, "エラー", Color.Red));
            }
        }

        private void ApplyAuthHeaders(HttpWebRequest req)
        {
            if (!string.IsNullOrEmpty(config.Username))
            {
                string auth = Convert.ToBase64String(Encoding.UTF8.GetBytes(config.Username + ":" + config.Password));
                req.Headers.Add("X-Cybozu-Authorization", auth);
            }
            if (config.UseBasicAuth && !string.IsNullOrEmpty(config.BasicUsername))
            {
                string bAuth = Convert.ToBase64String(Encoding.UTF8.GetBytes(config.BasicUsername + ":" + config.BasicPassword));
                req.Headers.Add("Authorization", "Basic " + bAuth);
            }
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            base.OnPaint(e);
            var g = e.Graphics;
            g.SmoothingMode = SmoothingMode.AntiAlias;
            g.TextRenderingHint = System.Drawing.Text.TextRenderingHint.ClearTypeGridFit;

            int w = this.ClientSize.Width;
            int h = this.ClientSize.Height;
            float scale = config.FontScale;

            // 1. ホワイトボードアルミフレーム＆板面
            using (var path = GetRoundedRect(new Rectangle(2, 2, w - 5, h - 5), 18))
            {
                using (var fill = new SolidBrush(Color.White))
                {
                    g.FillPath(fill, path);
                }
                using (var pen = new Pen(Color.FromArgb(90, 101, 114), 5))
                {
                    g.DrawPath(pen, path);
                }
            }

            int top = 8;

            // 2. 最上部コントロールバー
            DrawTopControls(g, top, w);

            top += 20;

            // 3. タイトル「行 動 予 定 表」
            float titleSize = Math.Max(13f, 17f * scale);
            using (var fontTitle = new Font("Meiryo", titleSize, FontStyle.Bold))
            using (var brushTitle = new SolidBrush(Color.FromArgb(17, 24, 39)))
            {
                string title = "行 動 予 定 表";
                var size = g.MeasureString(title, fontTitle);
                g.DrawString(title, fontTitle, brushTitle, (w - size.Width) / 2, top);
            }
            top += (int)(34 * scale);

            // 4. 日付「〇月 〇日 (曜日)」
            string[] wdays = { "日", "月", "火", "水", "木", "金", "土" };
            string dateStr = string.Format("{0}月 {1}日 ({2})", currentDate.Month, currentDate.Day, wdays[(int)currentDate.DayOfWeek]);
            float dateFontSize = Math.Max(9.5f, 10.5f * scale);
            using (var fontDate = new Font("Meiryo", dateFontSize, FontStyle.Bold))
            using (var brushDate = new SolidBrush(Color.FromArgb(17, 24, 39)))
            using (var penLine = new Pen(Color.FromArgb(17, 24, 39), 2))
            {
                int dLeft = 18;
                g.DrawString(dateStr, fontDate, brushDate, dLeft, top);
                var dSize = g.MeasureString(dateStr, fontDate);
                g.DrawLine(penLine, dLeft, top + dSize.Height + 1, dLeft + dSize.Width + 14, top + dSize.Height + 1);
            }
            top += (int)(28 * scale);

            // 5. カラム見出し（氏名・行先・帰社時間）
            int leftName = 16;
            int widthName = (int)(88 * scale);
            int widthTime = (int)(65 * scale);
            int leftTime = w - 16 - widthTime;
            int leftDest = leftName + widthName + 8;
            int widthDest = Math.Max(50, leftTime - leftDest - 8);

            float headerFontSize = Math.Max(9.5f, 10.5f * scale);
            using (var fontHeader = new Font("Meiryo", headerFontSize, FontStyle.Bold))
            using (var brushHeader = new SolidBrush(Color.FromArgb(17, 24, 39)))
            using (var penLine = new Pen(Color.FromArgb(17, 24, 39), 1.5f))
            {
                g.DrawString("氏名", fontHeader, brushHeader, leftName, top);
                g.DrawString("行先", fontHeader, brushHeader, leftDest, top);
                g.DrawString("帰社時間", fontHeader, brushHeader, leftTime - 2, top);
                top += (int)(22 * scale);
                g.DrawLine(penLine, leftName, top, leftTime + widthTime, top);
            }
            top += 6;

            // 6. 行リスト描画
            int rowHeight = (int)(34 * scale);
            int bottomMargin = 56;
            int availableHeight = h - top - bottomMargin;
            int visibleRows = Math.Max(1, availableHeight / rowHeight);

            float rowNameSize = Math.Max(9f, 10f * scale);
            float rowDestSize = Math.Max(8.5f, 9.5f * scale);
            float rowTimeSize = Math.Max(9f, 10f * scale);
            float badgeFontSize = Math.Max(8f, 8.5f * scale);

            using (var fontRowName = new Font("Meiryo", rowNameSize, FontStyle.Bold))
            using (var fontRowDest = new Font("Meiryo", rowDestSize, FontStyle.Regular))
            using (var fontRowTime = new Font("Segoe UI", rowTimeSize, FontStyle.Bold))
            using (var fontBadge = new Font("Meiryo", badgeFontSize, FontStyle.Bold))
            using (var penRowLine = new Pen(Color.FromArgb(113, 113, 122), 1f))
            using (var brushColon = new SolidBrush(Color.FromArgb(148, 163, 184)))
            {
                for (int i = 0; i < visibleRows; i++)
                {
                    int rowY = top + i * rowHeight;
                    if (rowY + rowHeight > h - bottomMargin + 10) break;

                    if (i < members.Count)
                    {
                        var m = members[i];

                        // 氏名（クリック可能であることを示すアンダーラインとスタイル）
                        using (var bName = new SolidBrush(Color.FromArgb(17, 24, 39)))
                        {
                            g.DrawString(m.Name, fontRowName, bName, leftName, rowY + 4);
                        }

                        // 行先（年休・在宅の特別バッジ描画対応）
                        float destCurrentX = leftDest;

                        if (m.IsNenkyu)
                        {
                            DrawBadge(g, "年休", fontBadge, Color.FromArgb(220, 38, 38), Color.White, destCurrentX, rowY + 4, scale);
                            destCurrentX += (int)(38 * scale);
                        }
                        else if (m.IsZaitaku)
                        {
                            DrawBadge(g, "在宅", fontBadge, Color.FromArgb(250, 204, 21), Color.FromArgb(17, 24, 39), destCurrentX, rowY + 4, scale);
                            destCurrentX += (int)(38 * scale);
                        }

                        string destText = m.Destination;
                        if ((m.IsNenkyu && destText == "年休") || (m.IsZaitaku && destText == "在宅"))
                        {
                            destText = "";
                        }

                        if (!string.IsNullOrEmpty(destText))
                        {
                            using (var bDest = new SolidBrush(m.InkColor))
                            {
                                float remainWidth = Math.Max(20, (leftDest + widthDest) - destCurrentX);
                                var rectDest = new RectangleF(destCurrentX, rowY + 5, remainWidth, rowHeight - 6);
                                var sf = new StringFormat { Trimming = StringTrimming.EllipsisCharacter, FormatFlags = StringFormatFlags.NoWrap };
                                g.DrawString(destText, fontRowDest, bDest, rectDest, sf);
                            }
                        }

                        // 帰社時間
                        using (var bTime = new SolidBrush(m.InkColor))
                        {
                            var tSize = g.MeasureString(m.ReturnTime, fontRowTime);
                            float tX = leftTime + (widthTime - tSize.Width) / 2;
                            g.DrawString(m.ReturnTime, fontRowTime, bTime, tX, rowY + 4);
                        }
                    }
                    else
                    {
                        var cSize = g.MeasureString(":", fontRowTime);
                        float cX = leftTime + (widthTime - cSize.Width) / 2;
                        g.DrawString(":", fontRowTime, brushColon, cX, rowY + 4);
                    }

                    int lineY = rowY + rowHeight - 4;
                    g.DrawLine(penRowLine, leftName, lineY, leftName + widthName - 4, lineY);
                    g.DrawLine(penRowLine, leftDest, lineY, leftDest + widthDest - 4, lineY);
                    g.DrawLine(penRowLine, leftTime, lineY, leftTime + widthTime, lineY);
                }
            }

            // 7. 右下のマーカー＆イレーザー入れポケット
            DrawMarkerPocket(g, w - 74, h - 54);

            // 8. 左下ステータス
            using (var fontStatus = new Font("Segoe UI", 8))
            using (var brushStatus = new SolidBrush(Color.FromArgb(148, 163, 184)))
            {
                string st = string.Format("更新: {0:HH:mm} {1}", DateTime.Now, config.MockMode ? "(デモ)" : "");
                g.DrawString(st, fontStatus, brushStatus, 16, h - 20);
            }
        }

        private void DrawBadge(Graphics g, string text, Font font, Color bgColor, Color textColor, float x, float y, float scale)
        {
            var size = g.MeasureString(text, font);
            int badgeW = (int)Math.Max(32 * scale, size.Width + 6 * scale);
            int badgeH = (int)(20 * scale);

            using (var path = GetRoundedRect(new Rectangle((int)x, (int)y, badgeW, badgeH), 4))
            using (var bBg = new SolidBrush(bgColor))
            using (var bText = new SolidBrush(textColor))
            {
                g.FillPath(bBg, path);
                float tx = x + (badgeW - size.Width) / 2;
                float ty = y + (badgeH - size.Height) / 2;
                g.DrawString(text, font, bText, tx, ty);
            }
        }

        private void DrawRefreshIcon(Graphics g, Rectangle r, Color color)
        {
            var sm = g.SmoothingMode;
            g.SmoothingMode = SmoothingMode.AntiAlias;

            float cx = r.X + r.Width / 2f;
            float cy = r.Y + r.Height / 2f;
            float radius = 4.8f;

            using (var pen = new Pen(color, 1.8f))
            {
                g.DrawArc(pen, cx - radius, cy - radius, radius * 2f, radius * 2f, -30f, 290f);
            }

            using (var brush = new SolidBrush(color))
            {
                PointF[] arrow = new PointF[]
                {
                    new PointF(cx + 1.2f, cy - radius - 3.2f),
                    new PointF(cx + 6.2f, cy - radius + 0.5f),
                    new PointF(cx + 1.2f, cy - radius + 3.8f)
                };
                g.FillPolygon(brush, arrow);
            }

            g.SmoothingMode = sm;
        }

        private void DrawPinIcon(Graphics g, Rectangle r, bool isPinned, Color normalColor)
        {
            var sm = g.SmoothingMode;
            g.SmoothingMode = SmoothingMode.AntiAlias;

            float cx = r.X + r.Width / 2f;
            float cy = r.Y + r.Height / 2f;

            Color color = isPinned ? Color.FromArgb(2, 132, 199) : normalColor;

            using (var pen = new Pen(color, 1.5f))
            using (var brush = new SolidBrush(color))
            {
                // ピンの頭部ツマミ
                g.DrawLine(pen, cx - 3.5f, cy - 5f, cx + 3.5f, cy - 5f);

                // ピンの胴体
                PointF[] body = new PointF[]
                {
                    new PointF(cx - 2.5f, cy - 5f),
                    new PointF(cx + 2.5f, cy - 5f),
                    new PointF(cx + 1.2f, cy + 0.5f),
                    new PointF(cx - 1.2f, cy + 0.5f)
                };

                if (isPinned)
                {
                    g.FillPolygon(brush, body);
                }
                else
                {
                    g.DrawPolygon(pen, body);
                }

                // つば
                g.DrawLine(pen, cx - 3.5f, cy + 0.5f, cx + 3.5f, cy + 0.5f);

                // 針
                g.DrawLine(pen, cx, cy + 0.5f, cx, cy + 5.5f);
            }

            g.SmoothingMode = sm;
        }

        private void DrawTopControls(Graphics g, int y, int w)
        {
            using (var font = new Font("Segoe UI", 8))
            using (var brush = new SolidBrush(Color.FromArgb(100, 116, 139)))
            {
                rectPrevDay = new Rectangle(14, y, 18, 18);
                rectToday = new Rectangle(34, y, 28, 18);
                rectNextDay = new Rectangle(64, y, 18, 18);

                g.DrawString("◀", font, brush, rectPrevDay.X + 2, rectPrevDay.Y + 2);
                g.DrawString("今日", font, brush, rectToday.X, rectToday.Y + 2);
                g.DrawString("▶", font, brush, rectNextDay.X + 2, rectNextDay.Y + 2);

                int rx = w - 24;
                rectClose = new Rectangle(rx, y, 18, 18);
                rx -= 20;
                rectMinimize = new Rectangle(rx, y, 18, 18);
                rx -= 22;
                rectSettings = new Rectangle(rx, y, 18, 18);
                rx -= 22;
                rectPlus = new Rectangle(rx, y, 18, 18);
                rx -= 20;
                rectMinus = new Rectangle(rx, y, 18, 18);
                rx -= 22;
                rectRefresh = new Rectangle(rx, y, 18, 18);
                rx -= 22;
                rectPin = new Rectangle(rx, y, 18, 18);

                using (var fontClose = new Font("Segoe UI", 9, FontStyle.Bold))
                {
                    g.DrawString("✕", fontClose, brush, rectClose.X + 2, rectClose.Y);
                }
                using (var fontMin = new Font("Segoe UI", 9, FontStyle.Bold))
                {
                    g.DrawString("―", fontMin, brush, rectMinimize.X + 2, rectMinimize.Y);
                }
                g.DrawString("⚙", font, brush, rectSettings.X + 2, rectSettings.Y + 2);

                using (var fontZoom = new Font("Segoe UI", 10, FontStyle.Bold))
                {
                    g.DrawString("+", fontZoom, brush, rectPlus.X + 3, rectPlus.Y - 1);
                    g.DrawString("-", fontZoom, brush, rectMinus.X + 4, rectMinus.Y - 2);
                }

                // 🔄 -> ベクター描画
                DrawRefreshIcon(g, rectRefresh, Color.FromArgb(100, 116, 139));

                // 📌 -> ベクター描画（固定中はアクティブカラー）
                DrawPinIcon(g, rectPin, config.AlwaysOnTop, Color.FromArgb(100, 116, 139));
            }
        }

        private void DrawMarkerPocket(Graphics g, int x, int y)
        {
            using (var brush = new SolidBrush(Color.FromArgb(24, 24, 27)))
            {
                g.FillRectangle(brush, x + 8, y + 6, 6, 34);
            }
            using (var brush = new SolidBrush(Color.FromArgb(220, 38, 38)))
            {
                g.FillRectangle(brush, x + 17, y + 10, 6, 30);
            }
            using (var brushHandle = new SolidBrush(Color.FromArgb(37, 99, 235)))
            using (var brushFelt = new SolidBrush(Color.FromArgb(241, 245, 249)))
            using (var penFelt = new Pen(Color.FromArgb(203, 213, 225)))
            {
                g.FillRectangle(brushHandle, x + 28, y + 12, 22, 14);
                g.FillRectangle(brushFelt, x + 28, y + 26, 22, 14);
                g.DrawRectangle(penFelt, x + 28, y + 26, 22, 14);
            }
            using (var brushGlass = new SolidBrush(Color.FromArgb(170, 226, 232, 240)))
            using (var penGlass = new Pen(Color.FromArgb(148, 163, 184), 1.5f))
            {
                g.FillRectangle(brushGlass, x + 2, y + 20, 52, 26);
                g.DrawRectangle(penGlass, x + 2, y + 20, 52, 26);
            }
        }

        private int GetRowsTopY(float scale)
        {
            int top = 8 + 20; // コントロールバー
            top += (int)(34 * scale); // タイトル
            top += (int)(28 * scale); // 日付
            top += (int)(22 * scale); // カラム見出し
            top += 6; // マージン
            return top;
        }

        protected override void OnMouseMove(MouseEventArgs e)
        {
            base.OnMouseMove(e);
            int top = GetRowsTopY(config.FontScale);
            int rowHeight = (int)(34 * config.FontScale);
            bool isOverRow = false;

            for (int i = 0; i < members.Count; i++)
            {
                int rY = top + i * rowHeight;
                if (e.Y >= rY && e.Y < rY + rowHeight && e.X >= 12 && e.X <= this.ClientSize.Width - 12)
                {
                    isOverRow = true;
                    break;
                }
            }

            string toolTipText = "";
            bool isOverControl = false;

            if (rectPin.Contains(e.Location))
            {
                toolTipText = config.AlwaysOnTop ? "最前面固定: ON (クリックで解除)" : "最前面に固定 (OFF)";
                isOverControl = true;
            }
            else if (rectRefresh.Contains(e.Location))
            {
                toolTipText = "今すぐ予定を更新";
                isOverControl = true;
            }
            else if (rectMinus.Contains(e.Location))
            {
                toolTipText = "文字サイズを縮小 (-)";
                isOverControl = true;
            }
            else if (rectPlus.Contains(e.Location))
            {
                toolTipText = "文字サイズを拡大 (+)";
                isOverControl = true;
            }
            else if (rectSettings.Contains(e.Location))
            {
                toolTipText = "設定 (ガルーン接続・表示ユーザー)";
                isOverControl = true;
            }
            else if (rectMinimize.Contains(e.Location))
            {
                toolTipText = "最小化";
                isOverControl = true;
            }
            else if (rectClose.Contains(e.Location))
            {
                toolTipText = "閉じる";
                isOverControl = true;
            }
            else if (rectPrevDay.Contains(e.Location))
            {
                toolTipText = "前日の予定";
                isOverControl = true;
            }
            else if (rectToday.Contains(e.Location))
            {
                toolTipText = "本日の予定に戻る";
                isOverControl = true;
            }
            else if (rectNextDay.Contains(e.Location))
            {
                toolTipText = "翌日の予定";
                isOverControl = true;
            }

            if (toolTipText != lastToolTipText)
            {
                lastToolTipText = toolTipText;
                if (!string.IsNullOrEmpty(toolTipText))
                {
                    buttonToolTip.SetToolTip(this, toolTipText);
                }
                else
                {
                    buttonToolTip.SetToolTip(this, null);
                }
            }

            if (isOverRow || isOverControl)
            {
                this.Cursor = Cursors.Hand;
            }
            else
            {
                this.Cursor = Cursors.Default;
            }
        }

        protected override void OnMouseDown(MouseEventArgs e)
        {
            base.OnMouseDown(e);

            if (e.Button == MouseButtons.Left)
            {
                if (rectClose.Contains(e.Location))
                {
                    ConfirmAndClose();
                    return;
                }
                if (rectMinimize.Contains(e.Location))
                {
                    this.WindowState = FormWindowState.Minimized;
                    return;
                }
                if (rectSettings.Contains(e.Location))
                {
                    OpenSettings();
                    return;
                }
                if (rectMinus.Contains(e.Location))
                {
                    config.FontScale = Math.Max(0.7f, (float)Math.Round(config.FontScale - 0.1f, 2));
                    config.Save();
                    this.Invalidate();
                    return;
                }
                if (rectPlus.Contains(e.Location))
                {
                    config.FontScale = Math.Min(1.8f, (float)Math.Round(config.FontScale + 0.1f, 2));
                    config.Save();
                    this.Invalidate();
                    return;
                }
                if (rectRefresh.Contains(e.Location))
                {
                    LoadData();
                    return;
                }
                if (rectPin.Contains(e.Location))
                {
                    config.AlwaysOnTop = !config.AlwaysOnTop;
                    this.TopMost = config.AlwaysOnTop;
                    config.Save();
                    this.Invalidate();
                    return;
                }
                if (rectPrevDay.Contains(e.Location))
                {
                    currentDate = currentDate.AddDays(-1);
                    LoadData();
                    return;
                }
                if (rectToday.Contains(e.Location))
                {
                    currentDate = DateTime.Today;
                    LoadData();
                    return;
                }
                if (rectNextDay.Contains(e.Location))
                {
                    currentDate = currentDate.AddDays(1);
                    LoadData();
                    return;
                }

                // 氏名・行クリック判定 -> そのユーザーの1日の全スケジュールを表示！
                int top = GetRowsTopY(config.FontScale);
                int rowHeight = (int)(34 * config.FontScale);
                for (int i = 0; i < members.Count; i++)
                {
                    int rY = top + i * rowHeight;
                    if (e.Y >= rY && e.Y < rY + rowHeight)
                    {
                        var m = members[i];
                        ShowUserDaySchedule(m);
                        return;
                    }
                }

                // ボード上のドラッグ移動
                ReleaseCapture();
                SendMessage(this.Handle, WM_NCLBUTTONDOWN, HT_CAPTION, 0);
            }
        }

        private void ShowUserDaySchedule(MemberStatus m)
        {
            string dateTitle = string.Format("{0}月{1}日", currentDate.Month, currentDate.Day);
            using (var dlg = new DayScheduleDialog(m, dateTitle))
            {
                dlg.ShowDialog(this);
            }
        }

        private void ConfirmAndClose()
        {
            var res = MessageBox.Show(this, "行動予定表を終了しますか？", "終了の確認", MessageBoxButtons.YesNo, MessageBoxIcon.Question);
            if (res == DialogResult.Yes)
            {
                SaveWindowState();
                this.Dispose();
                Application.Exit();
            }
        }

        private void SaveWindowState()
        {
            if (this.WindowState == FormWindowState.Normal)
            {
                config.WindowWidth = this.Width;
                config.WindowHeight = this.Height;
                config.WindowX = this.Location.X;
                config.WindowY = this.Location.Y;
                config.AlwaysOnTop = this.TopMost;
                config.Save();
            }
        }

        private void OpenSettings()
        {
            using (var dlg = new SettingsForm(config))
            {
                if (dlg.ShowDialog(this) == DialogResult.OK)
                {
                    config.Save();
                    int minutes = config.RefreshIntervalMinutes > 0 ? config.RefreshIntervalMinutes : 20;
                    autoTimer.Interval = minutes * 60 * 1000;
                    LoadData();
                }
            }
        }

        protected override void OnFormClosing(FormClosingEventArgs e)
        {
            SaveWindowState();
            base.OnFormClosing(e);
        }

        private GraphicsPath GetRoundedRect(Rectangle bounds, int radius)
        {
            int diameter = radius * 2;
            Size size = new Size(diameter, diameter);
            Rectangle arc = new Rectangle(bounds.Location, size);
            GraphicsPath path = new GraphicsPath();

            if (radius == 0)
            {
                path.AddRectangle(bounds);
                return path;
            }

            path.AddArc(arc, 180, 90);
            arc.X = bounds.Right - diameter;
            path.AddArc(arc, 270, 90);
            arc.Y = bounds.Bottom - diameter;
            path.AddArc(arc, 0, 90);
            arc.X = bounds.Left;
            path.AddArc(arc, 90, 90);
            path.CloseFigure();
            return path;
        }
    }

    /// <summary>
    /// 氏名クリック時に1日の全スケジュールを表示する専用ダイアログ
    /// </summary>
    public class DayScheduleDialog : Form
    {
        public DayScheduleDialog(MemberStatus member, string dateStr)
        {
            this.Text = string.Format("【{0}】 {1} のスケジュール一覧", member.Name, dateStr);
            this.Size = new Size(430, 520);
            this.FormBorderStyle = FormBorderStyle.FixedDialog;
            this.StartPosition = FormStartPosition.CenterParent;
            this.MaximizeBox = false;
            this.MinimizeBox = false;
            this.BackColor = Color.FromArgb(241, 245, 249);

            int headerHeight = 66;
            int footerHeight = 46;

            // 1. ヘッダーパネル（上部固定、高さ66px）
            var pnlHeader = new Panel
            {
                Location = new Point(0, 0),
                Size = new Size(this.ClientSize.Width, headerHeight),
                Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right,
                BackColor = Color.White
            };
            pnlHeader.Paint += (s, e) =>
            {
                using (var pen = new Pen(Color.FromArgb(226, 232, 240), 1))
                {
                    e.Graphics.DrawLine(pen, 0, headerHeight - 1, pnlHeader.Width, headerHeight - 1);
                }
            };

            var lblName = new Label
            {
                Text = member.Name,
                Font = new Font("Meiryo", 13f, FontStyle.Bold),
                Location = new Point(16, 10),
                AutoSize = true,
                ForeColor = Color.FromArgb(15, 23, 42)
            };
            pnlHeader.Controls.Add(lblName);

            // 現在の状態バッジ
            string statusText = member.Destination;
            Color badgeBg = Color.FromArgb(220, 252, 231);
            Color badgeText = Color.FromArgb(22, 163, 74);
            if (member.IsNenkyu)
            {
                statusText = "年休";
                badgeBg = Color.FromArgb(254, 226, 226);
                badgeText = Color.FromArgb(220, 38, 38);
            }
            else if (member.IsZaitaku)
            {
                statusText = "在宅";
                badgeBg = Color.FromArgb(254, 240, 138);
                badgeText = Color.FromArgb(161, 98, 7);
            }
            else if (member.Destination.Contains("外出"))
            {
                badgeBg = Color.FromArgb(255, 237, 213);
                badgeText = Color.FromArgb(234, 88, 12);
            }
            else if (member.Destination.Contains("会議") || member.Destination.Contains("面談"))
            {
                badgeBg = Color.FromArgb(219, 234, 254);
                badgeText = Color.FromArgb(37, 99, 235);
            }

            var lblStatus = new Label
            {
                Text = "現在: " + statusText + (member.ReturnTime != "―" && member.ReturnTime != "終日" ? " (〜" + member.ReturnTime + ")" : ""),
                Font = new Font("Meiryo", 9f, FontStyle.Bold),
                Location = new Point(16, 38),
                AutoSize = true,
                ForeColor = badgeText
            };
            pnlHeader.Controls.Add(lblStatus);
            this.Controls.Add(pnlHeader);

            // 2. 下部フッターパネル（下部固定、高さ46px）
            var pnlBottom = new Panel
            {
                Location = new Point(0, this.ClientSize.Height - footerHeight),
                Size = new Size(this.ClientSize.Width, footerHeight),
                Anchor = AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right,
                BackColor = Color.White
            };
            pnlBottom.Paint += (s, e) =>
            {
                using (var pen = new Pen(Color.FromArgb(226, 232, 240), 1))
                {
                    e.Graphics.DrawLine(pen, 0, 0, pnlBottom.Width, 0);
                }
            };

            var btnClose = new Button
            {
                Text = "閉じる",
                DialogResult = DialogResult.OK,
                Location = new Point(this.ClientSize.Width - 96, 8),
                Width = 82,
                Height = 28,
                Font = new Font("Meiryo", 9f),
                Anchor = AnchorStyles.Right | AnchorStyles.Top
            };
            this.AcceptButton = btnClose;
            this.CancelButton = btnClose;
            pnlBottom.Controls.Add(btnClose);
            this.Controls.Add(pnlBottom);

            // 3. メインのスケジュールリスト（ヘッダーの真下からフッターの真上まで）
            var pnlEvents = new Panel
            {
                Location = new Point(0, headerHeight),
                Size = new Size(this.ClientSize.Width, this.ClientSize.Height - headerHeight - footerHeight),
                Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right,
                AutoScroll = true,
                BackColor = Color.FromArgb(241, 245, 249)
            };

            int y = 12;

            if (member.DayEvents == null || member.DayEvents.Count == 0)
            {
                var lblEmpty = new Label
                {
                    Text = "本日の登録されたスケジュールはありません（終日在席）。",
                    Font = new Font("Meiryo", 10f, FontStyle.Regular),
                    ForeColor = Color.FromArgb(100, 116, 139),
                    Location = new Point(20, 30),
                    AutoSize = true
                };
                pnlEvents.Controls.Add(lblEmpty);
            }
            else
            {
                // カードの幅（スクロールバーの余裕を引いた幅: 幅 - 32px）
                int cardWidth = this.ClientSize.Width - 36;

                foreach (var ev in member.DayEvents)
                {
                    var card = new Panel
                    {
                        Location = new Point(14, y),
                        Width = cardWidth,
                        BackColor = Color.White,
                        BorderStyle = BorderStyle.None
                    };
                    card.Paint += (s, e) =>
                    {
                        using (var pen = new Pen(Color.FromArgb(203, 213, 225), 1))
                        {
                            e.Graphics.DrawRectangle(pen, 0, 0, card.Width - 1, card.Height - 1);
                        }
                    };

                    int cardY = 8;

                    // 時間帯 ＆ 現在進行中バッジ
                    string timeInfo = ev.TimeRange;
                    if (ev.IsCurrentActive) timeInfo += "  【現在進行中の予定】";

                    var lblTime = new Label
                    {
                        Text = "🕒 " + timeInfo,
                        Font = new Font("Segoe UI", 9f, ev.IsCurrentActive ? FontStyle.Bold : FontStyle.Regular),
                        ForeColor = ev.IsCurrentActive ? Color.FromArgb(220, 38, 38) : Color.FromArgb(71, 85, 105),
                        Location = new Point(10, cardY),
                        AutoSize = true
                    };
                    card.Controls.Add(lblTime);
                    cardY += 22;

                    // 件名
                    string titleText = ev.Subject;
                    if (!string.IsNullOrEmpty(ev.Menu))
                    {
                        titleText = string.Format("[{0}] {1}", ev.Menu, ev.Subject);
                    }

                    var lblTitle = new Label
                    {
                        Text = titleText,
                        Font = new Font("Meiryo", 10f, FontStyle.Bold),
                        ForeColor = Color.FromArgb(15, 23, 42),
                        Location = new Point(10, cardY),
                        Width = cardWidth - 20,
                        AutoSize = true
                    };
                    card.Controls.Add(lblTitle);
                    cardY += lblTitle.Height + 4;

                    // メモ・場所
                    if (!string.IsNullOrEmpty(ev.Notes))
                    {
                        var lblNotes = new Label
                        {
                            Text = "📍 " + ev.Notes,
                            Font = new Font("Meiryo", 8.5f, FontStyle.Regular),
                            ForeColor = Color.FromArgb(100, 116, 139),
                            Location = new Point(12, cardY),
                            Width = cardWidth - 24,
                            AutoSize = true
                        };
                        card.Controls.Add(lblNotes);
                        cardY += lblNotes.Height + 6;
                    }

                    card.Height = cardY + 4;
                    pnlEvents.Controls.Add(card);

                    y += card.Height + 10;
                }
            }

            // スクロール可能領域を確実に設定
            pnlEvents.AutoScrollMinSize = new Size(0, y + 10);
            this.Controls.Add(pnlEvents);

            // マウスホイールイベントをパネルにフォーカス
            this.Shown += (s, e) => { pnlEvents.Focus(); };
        }
    }

    public class SettingsForm : Form
    {
        private Config cfg;
        private CheckBox chkMock;
        private TextBox txtUrl;
        private TextBox txtUser;
        private TextBox txtPass;
        private CheckBox chkSsl;
        private CheckBox chkBasic;
        private TextBox txtBUser;
        private TextBox txtBPass;
        private ComboBox cmbInterval;

        private TextBox txtSearchKeyword;
        private Button btnSearch;
        private ComboBox cmbSearchResults;
        private Button btnAddUser;
        private Label lblSearchResultCount;

        private CheckedListBox chkListAddedUsers;
        private Button btnSelectAll;
        private Button btnDeselectAll;
        private Button btnRemoveUser;
        private Label lblAddedCount;

        private List<UserItem> currentAddedUsers = new List<UserItem>();
        private HashSet<string> currentCheckedIds = new HashSet<string>();

        public SettingsForm(Config c)
        {
            this.cfg = c;
            this.Text = "設定 - ガルーン行動予定表";
            this.Size = new Size(490, 640);
            this.FormBorderStyle = FormBorderStyle.FixedDialog;
            this.StartPosition = FormStartPosition.CenterParent;
            this.MaximizeBox = false;
            this.MinimizeBox = false;

            currentAddedUsers = new List<UserItem>(cfg.AddedUsers);
            currentCheckedIds = new HashSet<string>(cfg.CheckedUserIds);

            var tabControl = new TabControl { Dock = DockStyle.Fill };

            var tabConn = new TabPage("接続・動作設定");
            BuildConnTab(tabConn);
            tabControl.TabPages.Add(tabConn);

            var tabUsers = new TabPage("表示ユーザー設定");
            BuildUsersTab(tabUsers);
            tabControl.TabPages.Add(tabUsers);

            var pnlBottom = new Panel { Dock = DockStyle.Bottom, Height = 45 };
            var btnOk = new Button { Text = "保存して適用", DialogResult = DialogResult.OK, Location = new Point(250, 8), Width = 110, Height = 28 };
            btnOk.Click += (s, e) => { SaveSettings(); };
            var btnCancel = new Button { Text = "キャンセル", DialogResult = DialogResult.Cancel, Location = new Point(370, 8), Width = 90, Height = 28 };
            pnlBottom.Controls.Add(btnOk);
            pnlBottom.Controls.Add(btnCancel);

            this.Controls.Add(tabControl);
            this.Controls.Add(pnlBottom);

            RefreshAddedUsersList();
        }

        private void BuildConnTab(TabPage tab)
        {
            int y = 14;

            chkMock = new CheckBox { Text = "デモ（モック）モードを使用する", Checked = cfg.MockMode, Location = new Point(20, y), AutoSize = true, Font = new Font("Meiryo", 9, FontStyle.Bold), ForeColor = Color.FromArgb(2, 132, 199) };
            tab.Controls.Add(chkMock);
            y += 30;

            tab.Controls.Add(new Label { Text = "ガルーン URL:", Location = new Point(20, y), AutoSize = true });
            y += 18;
            txtUrl = new TextBox { Text = cfg.GaroonUrl, Location = new Point(20, y), Width = 410 };
            tab.Controls.Add(txtUrl);
            y += 28;

            tab.Controls.Add(new Label { Text = "ログイン名:", Location = new Point(20, y), AutoSize = true });
            tab.Controls.Add(new Label { Text = "パスワード:", Location = new Point(230, y), AutoSize = true });
            y += 18;
            txtUser = new TextBox { Text = cfg.Username, Location = new Point(20, y), Width = 190 };
            txtPass = new TextBox { Text = cfg.Password, PasswordChar = '*', Location = new Point(230, y), Width = 200 };
            tab.Controls.Add(txtUser);
            tab.Controls.Add(txtPass);
            y += 28;

            chkSsl = new CheckBox { Text = "SSL証明書を検証する（社内オレオレ証明書はOFF）", Checked = cfg.VerifySsl, Location = new Point(20, y), AutoSize = true };
            tab.Controls.Add(chkSsl);
            y += 24;

            chkBasic = new CheckBox { Text = "WebサーバーのBasic認証を使用する", Checked = cfg.UseBasicAuth, Location = new Point(20, y), AutoSize = true };
            tab.Controls.Add(chkBasic);
            y += 24;

            txtBUser = new TextBox { Text = cfg.BasicUsername, Location = new Point(20, y), Width = 190, Enabled = cfg.UseBasicAuth };
            txtBPass = new TextBox { Text = cfg.BasicPassword, PasswordChar = '*', Location = new Point(230, y), Width = 200, Enabled = cfg.UseBasicAuth };
            chkBasic.CheckedChanged += (s, e) => { txtBUser.Enabled = chkBasic.Checked; txtBPass.Enabled = chkBasic.Checked; };
            tab.Controls.Add(txtBUser);
            tab.Controls.Add(txtBPass);
            y += 34;

            tab.Controls.Add(new Label { Text = "自動更新間隔:", Location = new Point(20, y + 2), AutoSize = true });
            cmbInterval = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList, Location = new Point(120, y), Width = 150 };
            cmbInterval.Items.AddRange(new object[] { "1分ごと", "5分ごと", "10分ごと", "20分ごと（標準）", "30分ごと", "60分ごと" });

            if (cfg.RefreshIntervalMinutes == 1) cmbInterval.SelectedIndex = 0;
            else if (cfg.RefreshIntervalMinutes == 5) cmbInterval.SelectedIndex = 1;
            else if (cfg.RefreshIntervalMinutes == 10) cmbInterval.SelectedIndex = 2;
            else if (cfg.RefreshIntervalMinutes == 30) cmbInterval.SelectedIndex = 4;
            else if (cfg.RefreshIntervalMinutes == 60) cmbInterval.SelectedIndex = 5;
            else cmbInterval.SelectedIndex = 3;

            tab.Controls.Add(cmbInterval);
        }

        private void BuildUsersTab(TabPage tab)
        {
            var pnlSearch = new GroupBox
            {
                Text = "1. ユーザーを検索して追加",
                Location = new Point(14, 10),
                Size = new Size(440, 115),
                Font = new Font("Meiryo", 9f, FontStyle.Bold)
            };

            var lblK = new Label { Text = "検索キーワード (氏名または社員コード):", Location = new Point(14, 22), AutoSize = true, Font = new Font("Meiryo", 8.5f, FontStyle.Regular) };
            pnlSearch.Controls.Add(lblK);

            txtSearchKeyword = new TextBox { Location = new Point(14, 42), Width = 290, Font = new Font("Meiryo", 9f, FontStyle.Regular) };
            txtSearchKeyword.KeyDown += (s, e) => { if (e.KeyCode == Keys.Enter) { DoSearchUsers(); e.SuppressKeyPress = true; } };
            pnlSearch.Controls.Add(txtSearchKeyword);

            btnSearch = new Button { Text = "🔍 検索", Location = new Point(310, 40), Width = 114, Height = 26, Font = new Font("Meiryo", 8.5f, FontStyle.Regular) };
            btnSearch.Click += (s, e) => { DoSearchUsers(); };
            pnlSearch.Controls.Add(btnSearch);

            lblSearchResultCount = new Label { Text = "検索結果から選択:", Location = new Point(14, 76), AutoSize = true, Font = new Font("Meiryo", 8.5f, FontStyle.Regular) };
            pnlSearch.Controls.Add(lblSearchResultCount);

            cmbSearchResults = new ComboBox
            {
                Location = new Point(130, 74),
                Width = 200,
                DropDownStyle = ComboBoxStyle.DropDownList,
                Font = new Font("Meiryo", 8.5f, FontStyle.Regular)
            };
            pnlSearch.Controls.Add(cmbSearchResults);

            btnAddUser = new Button
            {
                Text = "➕ 追加",
                Location = new Point(340, 72),
                Width = 84,
                Height = 26,
                Font = new Font("Meiryo", 8.5f, FontStyle.Bold),
                ForeColor = Color.FromArgb(2, 132, 199)
            };
            btnAddUser.Click += (s, e) => { AddSelectedUserFromSearch(); };
            pnlSearch.Controls.Add(btnAddUser);

            tab.Controls.Add(pnlSearch);

            var pnlList = new GroupBox
            {
                Text = "2. 行動予定表に表示するメンバー (チェックした人のみ表示)",
                Location = new Point(14, 135),
                Size = new Size(440, 395),
                Font = new Font("Meiryo", 9f, FontStyle.Bold)
            };

            lblAddedCount = new Label
            {
                Text = "登録中: 0人",
                Location = new Point(14, 24),
                AutoSize = true,
                Font = new Font("Meiryo", 8.5f, FontStyle.Regular),
                ForeColor = Color.FromArgb(71, 85, 105)
            };
            pnlList.Controls.Add(lblAddedCount);

            btnSelectAll = new Button { Text = "全選択", Location = new Point(180, 20), Width = 65, Height = 24, Font = new Font("Meiryo", 8f, FontStyle.Regular) };
            btnSelectAll.Click += (s, e) => { SetAllChecked(true); };
            pnlList.Controls.Add(btnSelectAll);

            btnDeselectAll = new Button { Text = "全解除", Location = new Point(250, 20), Width = 65, Height = 24, Font = new Font("Meiryo", 8f, FontStyle.Regular) };
            btnDeselectAll.Click += (s, e) => { SetAllChecked(false); };
            pnlList.Controls.Add(btnDeselectAll);

            btnRemoveUser = new Button { Text = "🗑 削除", Location = new Point(330, 20), Width = 94, Height = 24, Font = new Font("Meiryo", 8f, FontStyle.Regular), ForeColor = Color.FromArgb(220, 38, 38) };
            btnRemoveUser.Click += (s, e) => { RemoveSelectedUser(); };
            pnlList.Controls.Add(btnRemoveUser);

            chkListAddedUsers = new CheckedListBox
            {
                Location = new Point(14, 50),
                Size = new Size(410, 330),
                CheckOnClick = true,
                Font = new Font("Meiryo", 9.5f, FontStyle.Regular)
            };
            chkListAddedUsers.ItemCheck += (s, e) =>
            {
                if (e.Index >= 0 && e.Index < chkListAddedUsers.Items.Count)
                {
                    var u = chkListAddedUsers.Items[e.Index] as UserItem;
                    if (u != null)
                    {
                        if (e.NewValue == CheckState.Checked)
                            currentCheckedIds.Add(u.Id);
                        else
                            currentCheckedIds.Remove(u.Id);
                    }
                }
            };
            pnlList.Controls.Add(chkListAddedUsers);

            tab.Controls.Add(pnlList);
        }

        private void DoSearchUsers()
        {
            string keyword = txtSearchKeyword.Text.Trim();
            if (string.IsNullOrEmpty(keyword))
            {
                MessageBox.Show(this, "検索キーワード（氏名または社員コード）を入力してください。", "案内", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }

            btnSearch.Enabled = false;
            btnSearch.Text = "検索中...";
            cmbSearchResults.Items.Clear();

            List<UserItem> found = SearchUsersFromGaroon(keyword);
            btnSearch.Enabled = true;
            btnSearch.Text = "🔍 検索";

            if (found.Count == 0)
            {
                lblSearchResultCount.Text = "該当なし (0件):";
                MessageBox.Show(this, string.Format("「{0}」に一致するユーザーは見つかりませんでした。", keyword), "検索結果", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }

            lblSearchResultCount.Text = string.Format("検索結果 ({0}件):", found.Count);
            foreach (var u in found)
            {
                cmbSearchResults.Items.Add(u);
            }
            cmbSearchResults.SelectedIndex = 0;
        }

        private List<UserItem> SearchUsersFromGaroon(string keyword)
        {
            var list = new List<UserItem>();

            if (chkMock.Checked)
            {
                var allMock = new List<UserItem>
                {
                    new UserItem("1", "山田 太郎", "yamada"),
                    new UserItem("2", "佐藤 美咲", "sato"),
                    new UserItem("3", "鈴木 一郎", "suzuki"),
                    new UserItem("4", "高橋 健太", "takahashi"),
                    new UserItem("5", "伊藤 翔太", "ito"),
                    new UserItem("6", "渡辺 裕子", "watanabe"),
                    new UserItem("7", "中村 健二", "nakamura"),
                    new UserItem("8", "小林 真由美", "kobayashi"),
                    new UserItem("9", "加藤 拓也", "kato"),
                    new UserItem("10", "吉田 陽子", "yoshida"),
                    new UserItem("11", "田中 誠", "tanaka"),
                    new UserItem("12", "松本 潤", "matsumoto")
                };

                string kw = keyword.ToLower();
                foreach (var u in allMock)
                {
                    if (u.Name.ToLower().Contains(kw) || u.Code.ToLower().Contains(kw))
                    {
                        list.Add(u);
                    }
                }
                return list;
            }

            try
            {
                string baseUrl = txtUrl.Text.Trim().TrimEnd('/');
                if (!baseUrl.EndsWith("/api/v1"))
                {
                    if (baseUrl.Contains("grn.cgi") || baseUrl.Contains("grn.exe"))
                        baseUrl += "/api/v1";
                    else
                        baseUrl += "/api/v1";
                }

                string encodedKw = Uri.EscapeDataString(keyword);
                string searchUrl = string.Format("{0}/base/users?name={1}&limit=50", baseUrl, encodedKw);

                var req = (HttpWebRequest)WebRequest.Create(searchUrl);
                req.Timeout = 8000;
                ApplyAuthToRequest(req);

                using (var resp = req.GetResponse())
                using (var reader = new StreamReader(resp.GetResponseStream(), Encoding.UTF8))
                {
                    string json = reader.ReadToEnd();
                    var serializer = new JavaScriptSerializer();
                    var data = serializer.Deserialize<Dictionary<string, object>>(json);
                    if (data != null && data.ContainsKey("users"))
                    {
                        var arr = data["users"] as ArrayList;
                        if (arr != null)
                        {
                            foreach (Dictionary<string, object> item in arr)
                            {
                                string id = item.ContainsKey("id") ? item["id"].ToString() : "";
                                string name = item.ContainsKey("name") ? (item["name"] as string) : "";
                                string code = item.ContainsKey("code") ? (item["code"] as string) : "";
                                list.Add(new UserItem(id, name, code));
                            }
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show(this, "ガルーン検索エラー:\n" + ex.Message, "エラー", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }

            return list;
        }

        private void ApplyAuthToRequest(HttpWebRequest req)
        {
            if (!string.IsNullOrEmpty(txtUser.Text))
            {
                string auth = Convert.ToBase64String(Encoding.UTF8.GetBytes(txtUser.Text + ":" + txtPass.Text));
                req.Headers.Add("X-Cybozu-Authorization", auth);
            }
            if (chkBasic.Checked && !string.IsNullOrEmpty(txtBUser.Text))
            {
                string bAuth = Convert.ToBase64String(Encoding.UTF8.GetBytes(txtBUser.Text + ":" + txtBPass.Text));
                req.Headers.Add("Authorization", "Basic " + bAuth);
            }
        }

        private void AddSelectedUserFromSearch()
        {
            var selected = cmbSearchResults.SelectedItem as UserItem;
            if (selected == null)
            {
                MessageBox.Show(this, "追加したいユーザーを検索結果から選んでください。", "案内", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }

            if (currentAddedUsers.Exists(u => u.Id == selected.Id))
            {
                MessageBox.Show(this, string.Format("「{0}」は既に下の一覧に追加されています。", selected.Name), "確認", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }

            currentAddedUsers.Add(selected);
            currentCheckedIds.Add(selected.Id);

            RefreshAddedUsersList();

            for (int i = 0; i < chkListAddedUsers.Items.Count; i++)
            {
                var u = chkListAddedUsers.Items[i] as UserItem;
                if (u != null && u.Id == selected.Id)
                {
                    chkListAddedUsers.SelectedIndex = i;
                    break;
                }
            }
        }

        private void RemoveSelectedUser()
        {
            int idx = chkListAddedUsers.SelectedIndex;
            if (idx < 0 || idx >= chkListAddedUsers.Items.Count)
            {
                MessageBox.Show(this, "一覧から削除したいユーザーを選択してください。", "案内", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }

            var u = chkListAddedUsers.Items[idx] as UserItem;
            if (u != null)
            {
                currentAddedUsers.RemoveAll(item => item.Id == u.Id);
                currentCheckedIds.Remove(u.Id);
                RefreshAddedUsersList();
            }
        }

        private void RefreshAddedUsersList()
        {
            chkListAddedUsers.BeginUpdate();
            chkListAddedUsers.Items.Clear();

            foreach (var u in currentAddedUsers)
            {
                bool isChecked = currentCheckedIds.Contains(u.Id);
                chkListAddedUsers.Items.Add(u, isChecked);
            }

            chkListAddedUsers.EndUpdate();
            lblAddedCount.Text = string.Format("登録中: {0}人 (チェック: {1}人)", currentAddedUsers.Count, currentCheckedIds.Count);
        }

        private void SetAllChecked(bool check)
        {
            for (int i = 0; i < chkListAddedUsers.Items.Count; i++)
            {
                chkListAddedUsers.SetItemChecked(i, check);
                var u = chkListAddedUsers.Items[i] as UserItem;
                if (u != null)
                {
                    if (check) currentCheckedIds.Add(u.Id);
                    else currentCheckedIds.Remove(u.Id);
                }
            }
            lblAddedCount.Text = string.Format("登録中: {0}人 (チェック: {1}人)", currentAddedUsers.Count, currentCheckedIds.Count);
        }

        private void SaveSettings()
        {
            cfg.MockMode = chkMock.Checked;
            cfg.GaroonUrl = txtUrl.Text;
            cfg.Username = txtUser.Text;
            cfg.Password = txtPass.Text;
            cfg.VerifySsl = chkSsl.Checked;
            cfg.UseBasicAuth = chkBasic.Checked;
            cfg.BasicUsername = txtBUser.Text;
            cfg.BasicPassword = txtBPass.Text;

            int[] intervals = { 1, 5, 10, 20, 30, 60 };
            cfg.RefreshIntervalMinutes = intervals[cmbInterval.SelectedIndex];

            cfg.AddedUsers.Clear();
            cfg.AddedUsers.AddRange(currentAddedUsers);

            cfg.CheckedUserIds.Clear();
            cfg.CheckedUserIds.AddRange(currentCheckedIds);
        }
    }

    static class Program
    {
        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new WhiteboardForm());
        }
    }
}
