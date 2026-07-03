"""
download_pdfs.py — 批次下載國北教教務處法規 PDF（以標題命名）
==============================================================
【用途】
    方式 B 大規模更新時使用，一次重新下載所有官方法規 PDF。
    日常新增單份文件請改用 app.py 管理員介面上傳，不需執行此腳本。

【使用方式】
    python download_pdfs.py

【更新法規連結】
    若法規有新版本，修改下方 PDF_LIST 對應的 URL 即可。

PDF 會下載到 regulations/ 資料夾，檔名為法規標題。
已存在的檔案會自動略過（斷點續傳）。
失敗的連結會記錄在 download_failed.txt。
"""

import re
import time
import requests
from pathlib import Path
from urllib.parse import urlparse

OUTPUT_DIR = Path("regulations")
FAILED_LOG = Path("download_failed.txt")
BASE_URL   = "https://academicntue.ntue.edu.tw"
DELAY      = 1.0

OUTPUT_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
}

def safe_filename(title: str) -> str:
    """將標題轉為合法檔名（移除不允許的字元）"""
    # 移除 Windows/Mac 不允許的字元
    name = re.sub(r'[\\/:*?"<>|]', "", title)
    # 移除括號內的說明文字（如「PDF開啟檔案」）
    name = re.sub(r'[（(][^）)]*[）)]', "", name)
    # 壓縮多餘空白
    name = re.sub(r'\s+', " ", name).strip()
    # 限制長度
    if len(name) > 80:
        name = name[:80]
    return name + ".pdf"


# ── URL → 標題 對應表 ─────────────────────────────
PDF_LIST = [
    # 本校學則
    ("/var/file/2/1002/img/17/RC001_1150616.pdf",   "國立臺北教育大學學則_115.6.16備查"),
    ("/var/file/2/1002/img/17/RC041.pdf",            "School Regulations 國立臺北教育大學學則"),
    # 畢業相關
    ("/var/file/2/1002/img/17/715940670.pdf",        "學生畢業資格審核作業要點_115.5.20"),
    ("/var/file/2/1002/img/38/RC028.pdf",            "畢業生學位證書發給原則"),
    ("/var/file/2/1002/img/38/RC029.pdf",            "學位證書更正及補發原則"),
    # 學籍相關
    ("/var/file/2/1002/img/17/883247033.pdf",        "學生轉系實施要點_115.5.20"),
    ("/var/file/2/1002/img/17/329577415.pdf",        "學士班學生修讀輔系辦法_115.5.20"),
    ("/var/file/2/1002/img/17/304934816.pdf",        "學生修讀雙主修辦法_115.5.20"),
    ("/var/file/2/1002/img/17/492575172.pdf",        "學生逕修讀博士學位要點"),
    ("/var/file/2/1002/img/38/RC025.pdf",            "學士班學生修讀碩士班課程要點"),
    ("/var/file/2/1002/img/38/RC025-5.pdf",          "Guidelines for Undergraduate Students Studying Masters Degree Program Courses"),
    # 期刊
    ("https://jepr.ntue.edu.tw/var/file/63/1063/img/661839926.pdf", "教育實踐與研究徵稿規則_115.3.31"),
    ("https://jepr.ntue.edu.tw/var/file/63/1063/img/441866571.pdf", "教育實踐與研究編輯委員會設置辦法"),
    # 選課相關
    ("/var/file/2/1002/img/17/674646578.pdf",        "學士班學生就學期間服役彈性修業實施要點"),
    # 獎學金相關
    ("/var/file/2/1002/img/367719903.pdf",           "優秀新生全額獎學金設置要點_115.02.25"),
    ("/var/file/2/1002/img/38/RC016.pdf",            "優秀新生全額獎學金設置要點_109.10.28"),
    ("/var/file/2/1002/img/38/RC016-1.pdf",          "優秀新生全額獎學金核獎及續領資格規定研商會議紀錄"),
    # 學術倫理
    ("/var/file/2/1002/img/381142166.pdf",           "學生學術倫理案件處理要點"),
    ("/var/file/2/1002/img/17/571627934.pdf",        "Guidelines for Cases of Student Violation of Academic Ethics"),
    # 其他
    ("/var/file/2/1002/img/38/RC017.pdf",            "專業表現優異學生甄選獎勵辦法"),
    ("/var/file/2/1002/img/38/RC039.pdf",            "頒授名譽博士學位辦法"),
    ("/var/file/2/1002/img/RC038.pdf",               "學生基本能力鑑定辦法"),
    # 學位授予相關
    ("/var/file/2/1002/img/303557221.pdf",           "論文指導關係規範原則"),
    ("/var/file/2/1002/img/257532923.pdf",           "日間學制學位授予暨研究生學位考試實施要點_115.2.25"),
    ("/var/file/2/1002/img/215899014.pdf",           "Full-time Program Degree Conferral and Graduate Student Degree Examination Regulations"),
    ("/var/file/2/1002/img/876722328.pdf",           "學位論文申請延後公開審核作業要點"),
    # 教師相關
    ("/var/file/2/1002/img/347305664.pdf",           "教師授課時數計算要點"),
    ("/var/file/2/1002/img/13/373512679.pdf",        "教務處辦理教師升等之校外學者專家遴選原則"),
    ("/var/file/2/1002/img/38/RC011.pdf",            "教學意見回饋與支持系統實施要點"),
    ("/var/file/2/1002/img/536039386.pdf",           "教學優良獎設置辦法_115.4.29"),
    ("/var/file/2/1002/img/266240126.pdf",           "教師請假支給代課鐘點費注意事項"),
    ("/var/file/2/1002/img/38/RC009-5.pdf",          "Leave Pay and Substitution Hourly Pay Guidelines for Teachers"),
    ("/var/file/2/1002/img/38/RC010-5.pdf",          "Teaching Excellence Award Implementation Guidelines"),
    ("/var/file/2/1002/img/38/RC012.pdf",            "遴聘業界專家協同教學實施要點"),
    ("/var/file/2/1002/img/102/816187115.pdf",       "教務處教學優良獎評選辦法_115.6.3"),
    ("/var/file/2/1002/img/13/233025652.pdf",        "內聘專任人員支援教學實施要點"),
    ("/var/file/2/1002/img/102/OfficeofAcademicAffairs,NationalTaipeiUniversityofEducation.pdf",
                                                     "Office of Academic Affairs Teacher Evaluation Standards"),
    ("/var/file/2/1002/img/13/514569254.pdf",        "教務處教師評鑑準則"),
    ("/var/file/2/1002/img/13/288831500.pdf",        "教務處教師評審委員會設置要點"),
    ("/var/file/2/1002/img/13/850004254.pdf",        "教務處專任教師聘任及升等審查準則"),
    # 課程相關
    ("/var/file/2/1002/img/720153027.pdf",           "遠距教學實施要點_114.4.16"),
    ("/var/file/2/1002/img/38/RC045.pdf",            "開設大學先修課程試辦計畫"),
    ("/var/file/2/1002/img/885154477.pdf",           "優課30教師創新教學補助計畫"),
    # 課務相關
    ("/var/file/2/1002/img/38/RC042.pdf",            "災害應變日間學制遠距教學及復課補課計畫"),
    ("/var/file/2/1002/img/38/RC032.pdf",            "開課實施辦法_115.04.22"),
    ("/var/file/2/1002/img/38/RC032-5.pdf",          "Course Offering Regulations"),
    ("/var/file/2/1002/img/38/887942466.pdf",        "課程委員會議提案原則_115.05.13"),
    ("/var/file/2/1002/img/798486400.pdf",           "學分學程設置辦法_115.04.22"),
    ("/var/file/2/1002/img/RC034.pdf",               "課程委員會設置要點_114.6.11"),
    ("/var/file/2/1002/img/38/RC036.pdf",            "課程大綱外審作業要點"),
    # 華語文中心
    ("/var/file/2/1002/img/24/338278638.pdf",        "華語文中心設置要點"),
    ("/var/file/2/1002/img/24/798465094.pdf",        "學人宿舍借用暨管理要點"),
    ("/var/file/2/1002/img/24/693489525.pdf",        "華語文中心校務基金兼職教學人員聘任要點"),
    # 學生選課相關
    ("/var/file/2/1002/img/555583703.pdf",           "自主學習課程實施辦法"),
    ("/var/file/2/1002/img/38/RC002.pdf",            "選課辦法_115.04.22"),
    ("/var/file/2/1002/img/38/RC002-5.pdf",          "Course Selection Regulations"),
    ("/var/file/2/1002/img/38/RC004.pdf",            "校際選課實施要點"),
    ("/var/file/2/1002/img/38/RC004-5.pdf",          "Implementation Guidelines for Interschool Class Selection"),
    ("/var/file/2/1002/img/38/RC006.pdf",            "學生申請停修課程實施要點"),
    ("/var/file/2/1002/img/38/RC006-5.pdf",          "Implementation Guidelines for Application to Withdraw from Courses"),
    ("/var/file/2/1002/img/100538642.pdf",           "日間學制暑期修課辦法_114.06.11"),
    ("/var/file/2/1002/img/38/RC007-5.pdf",          "Full-time Program Summer Course Regulations"),
    ("/var/file/2/1002/img/38/RC005.pdf",            "專業服務學習課程實施辦法"),
    ("/var/file/2/1002/img/38/RC003.pdf",            "外語課程修課實施辦法"),
    # 成績相關
    ("/var/file/2/1002/img/RC014-5.pdf",             "Regulations for the Conversion of Academic Performance and Ranking of Students"),
    ("/var/file/2/1002/img/RC013-5.pdf",             "Regulations for Student Grade Management"),
    ("/var/file/2/1002/img/16/RC015-5.pdf",          "Implementation Guidelines for Student Transfer of Credits"),
    ("/var/file/2/1002/img/38/RC014.pdf",            "學生學業成績轉換與排名規則"),
    ("/var/file/2/1002/img/RC013.pdf",               "學生成績管理辦法"),
    ("/var/file/2/1002/img/16/RC015.pdf",            "學生抵免學分實施要點"),
    # 學雜費相關
    ("/var/file/2/1002/img/38/RC030.pdf",            "雜費調整作業要點"),
    ("/var/file/2/1002/img/38/RC031.pdf",            "原住民族師資生就學費用全額減免實施要點"),
    # 研究生學位考試相關
    ("/var/file/2/1002/img/38/RC019.pdf",            "論文指導費及口試費支給原則"),
    # 招生相關
    ("/var/file/2/1002/img/111/505113179.pdf",       "新住民學生入學規定"),
    ("https://academicntue.ntue.edu.tw/var/file/2/1002/img/111/462974083.pdf", "學士班申請入學招生規定"),
    ("https://academicntue.ntue.edu.tw/var/file/2/1002/img/111/167668645.pdf", "運動績優學生單獨招生規定"),
    ("https://academicntue.ntue.edu.tw/var/file/2/1002/img/111/819776363.pdf", "辦理僑生及港澳生單獨招生規定"),
    ("https://academicntue.ntue.edu.tw/var/file/2/1002/img/111/559798002.pdf", "學士班特殊選才招生規定"),
    ("https://academicntue.ntue.edu.tw/var/file/2/1002/img/111/151217701.pdf", "招生名額調整作業要點"),
    ("https://academicntue.ntue.edu.tw/var/file/2/1002/img/111/337092548.pdf", "招生考試作業要點"),
    ("https://academicntue.ntue.edu.tw/var/file/2/1002/img/111/695741917.pdf", "轉學招生規定"),
    ("https://academicntue.ntue.edu.tw/var/file/2/1002/img/111/662989415.pdf", "研究所招生規定"),
    ("https://academicntue.ntue.edu.tw/var/file/2/1002/img/111/737015413.pdf", "辦理招生考試試務迴避要點"),
    ("https://academicntue.ntue.edu.tw/var/file/2/1002/img/111/306653043.pdf", "招生考試保密要點"),
    ("https://academicntue.ntue.edu.tw/var/file/2/1002/img/111/231115441.pdf", "招生考試命題準則"),
    ("https://academicntue.ntue.edu.tw/var/file/2/1002/img/111/703325645.pdf", "招生考試閱卷規則"),
    ("https://academicntue.ntue.edu.tw/var/file/2/1002/img/111/430583143.pdf", "招生考試闈場規則"),
    # Google Drive（音樂學系，需手動下載）
    # "https://drive.google.com/file/d/1tlMo27qkHQ6zOBwDp_MW6PakQ6Yy9sqS/view" → 音樂學系學士班單獨招生規定
]


def download(url: str, dest: Path) -> bool:
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        if r.status_code == 200:
            dest.write_bytes(r.content)
            return True
        print(f"  HTTP {r.status_code}")
        return False
    except Exception as e:
        print(f"  錯誤：{e}")
        return False


def main():
    # 組成完整 URL，去重
    tasks = []
    seen_urls = set()
    for href, title in PDF_LIST:
        url = href if href.startswith("http") else BASE_URL + href
        if url in seen_urls:
            continue
        seen_urls.add(url)
        fname = safe_filename(title)
        tasks.append((url, fname, title))

    print(f"共 {len(tasks)} 份 PDF，開始下載到 {OUTPUT_DIR}/\n")
    failed = []

    for i, (url, fname, title) in enumerate(tasks, 1):
        dest = OUTPUT_DIR / fname
        if dest.exists():
            print(f"[{i:02d}/{len(tasks)}] 已存在，略過：{fname}")
            continue

        print(f"[{i:02d}/{len(tasks)}] {title}")
        print(f"         → {fname}")
        ok = download(url, dest)
        if ok:
            size = dest.stat().st_size
            print(f"         ✅ {size/1024:.1f} KB")
        else:
            print(f"         ❌ 失敗")
            failed.append(f"{url}\t{title}")

        time.sleep(DELAY)

    print(f"\n{'='*55}")
    print(f"✅ 成功：{len(tasks) - len(failed)} 份")
    print(f"❌ 失敗：{len(failed)} 份")

    if failed:
        FAILED_LOG.write_text("\n".join(failed), encoding="utf-8")
        print(f"失敗清單已儲存至 {FAILED_LOG}")

    print("\n⚠️  注意：音樂學系學士班單獨招生規定 需手動從 Google Drive 下載，")
    print("     下載後命名為「音樂學系學士班單獨招生規定.pdf」放入 regulations/")


if __name__ == "__main__":
    main()
