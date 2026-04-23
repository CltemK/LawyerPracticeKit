/*  LegalFileRenamer — 法律文件重命名工具 (C + Win32 API)
 *  零依赖单文件，现代化 UI 设计
 */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <shlwapi.h>
#include <wchar.h>
#include <stdlib.h>
#include "resource.h"

#pragma comment(lib, "shlwapi.lib")

/* ---- Layout constants (pixels) ---- */
#define M           28          /* left/right margin */
#define WIN_W       540         /* window width */
#define CW          (WIN_W - 2 * M)
#define EH          32          /* edit height */
#define RH          24          /* radio height */
#define LH          16          /* label height */
#define GAP         6           /* gap between label and edit */
#define SEC         12          /* gap between sections */
#define CARD_PAD    14          /* card inner padding */
#define CARD_R      10          /* card corner radius */

/* Row positions — computed top-down */
#define R_HEADER    0
#define R_HEADER_H  64
#define R_BODY      (R_HEADER_H + 4)

#define R_ORIG_L    (R_BODY + 16)
#define R_ORIG_E    (R_ORIG_L + LH + GAP)
#define R_DATE_L    (R_ORIG_E + EH + SEC)
#define R_DATE_E    (R_DATE_L + LH + GAP)
#define R_CAT_L     (R_DATE_E + EH + SEC)
#define R_CAT_R     (R_CAT_L + LH + 4)
#define R_SUB_R     (R_CAT_R + RH + 2)
#define R_NAME_L    (R_SUB_R + RH + SEC)
#define R_NAME_E    (R_NAME_L + LH + GAP)
#define R_VER_L     (R_NAME_E + EH + SEC)
#define R_VER_E     (R_VER_L + LH + GAP)
#define R_PREV_L    (R_VER_E + EH + SEC)
#define R_PREV_E    (R_PREV_L + LH + GAP + 2)
#define R_PREV_H    38
#define R_BOTTOM    (R_PREV_E + R_PREV_H + 14)
#define WIN_H       (R_BOTTOM + 42)

/* ---- Modern Color Palette ---- */
#define COL_PRIMARY        RGB(0x1E, 0x3A, 0x5F)   /* Deep navy */
#define COL_PRIMARY_LIGHT  RGB(0x2C, 0x5A, 0x8A)   /* Lighter navy */
#define COL_ACCENT         RGB(0x3B, 0x82, 0xF6)   /* Bright blue */
#define COL_ACCENT_HOVER   RGB(0x60, 0xA5, 0xFA)   /* Hover blue */
#define COL_SUCCESS        RGB(0x22, 0xC5, 0x5E)   /* Green */
#define COL_SUCCESS_HOVER  RGB(0x4A, 0xDE, 0x80)   /* Hover green */
#define COL_DANGER         RGB(0xEF, 0x44, 0x44)    /* Red */
#define COL_DANGER_HOVER   RGB(0xF8, 0x71, 0x71)   /* Hover red */
#define COL_WARN_AMBER     RGB(0xF5, 0x9E, 0x0B)    /* Amber */
#define COL_WARN_BG        RGB(0xFF, 0xFB, 0xEB)    /* Light amber bg */
#define COL_WARN_BORDER    RGB(0xFE, 0xD7, 0xAA)    /* Amber border */

#define COL_BG             RGB(0xF8, 0xFA, 0xFC)    /* Page background */
#define COL_CARD           RGB(0xFF, 0xFF, 0xFF)    /* Card white */
#define COL_CARD_BORDER    RGB(0xE2, 0xE8, 0xF0)    /* Card border */
#define COL_INPUT_BG       RGB(0xF1, 0xF5, 0xF9)    /* Input background */
#define COL_INPUT_BORDER   RGB(0xCB, 0xD5, 0xE1)    /* Input border */
#define COL_INPUT_FOCUS    RGB(0x3B, 0x82, 0xF6)    /* Input focus border */

#define COL_TEXT_PRIMARY   RGB(0x1E, 0x29, 0x3B)    /* Dark text */
#define COL_TEXT_SECONDARY RGB(0x64, 0x74, 0x8B)    /* Secondary text */
#define COL_TEXT_MUTED     RGB(0x94, 0xA3, 0xB8)    /* Muted text */
#define COL_TEXT_READONLY  RGB(0x94, 0xA3, 0xB8)    /* Read-only text */
#define COL_TEXT_WHITE     RGB(0xFF, 0xFF, 0xFF)    /* White text */
#define COL_PREVIEW_TEXT   RGB(0x1E, 0x3A, 0x5F)    /* Preview text */
#define COL_PREVIEW_BG     RGB(0xEF, 0xF6, 0xFF)    /* Preview background */
#define COL_PREVIEW_BORDER RGB(0xBF, 0xDB, 0xFE)    /* Preview border */
#define COL_ERR            RGB(0xEF, 0x44, 0x44)     /* Error red */

/* ---- Globals ---- */
static HINSTANCE gInst;
static HFONT gFont, gFontB, gFontS, gFontTitle, gFontPrev, gFontBtn;
static HBRUSH gBrBg, gBrCard, gBrInput, gBrPreview, gBrWarnBg;
static HBRUSH gBrPrimary, gBrAccent, gBrSuccess, gBrDanger;
static HBRUSH gBrBtnOk, gBrBtnOkH, gBrBtnCancel, gBrBtnCancelH;
static HBRUSH gBrBtnFin, gBrBtnFinH;
static HPEN gPenCard, gPenInput, gPenInputFocus, gPenPreview, gPenWarn;
static HWND hSubDraft, hSubRev, hSubFinal;
static HWND hFinBg, hFinText, hFinBtn, hHeader;
static HWND hErr;
static HWND hBtnOk, hBtnCancel;
static BOOL gHoverOk, gHoverCancel, gHoverFin;

static wchar_t gPath[MAX_PATH], gName[MAX_PATH], gExt[32];
static BOOL gLawyer, gReady;

/* ---- Rounded Rectangle Helper ---- */
static void FillRoundRect(HDC dc, int x, int y, int w, int h, int r, HBRUSH br) {
    HRGN rgn = CreateRoundRectRgn(x, y, x + w, y + h, r * 2, r * 2);
    FillRgn(dc, rgn, br);
    DeleteObject(rgn);
}

static void FrameRoundRect(HDC dc, int x, int y, int w, int h, int r, HPEN pen) {
    HRGN rgn = CreateRoundRectRgn(x, y, x + w, y + h, r * 2, r * 2);
    HPEN old = (HPEN)SelectObject(dc, pen);
    HBRUSH oldBr = (HBRUSH)SelectObject(dc, GetStockObject(NULL_BRUSH));
    RoundRect(dc, x, y, x + w, y + h, r * 2, r * 2);
    SelectObject(dc, old);
    SelectObject(dc, oldBr);
}

/* ---- Helpers ---- */
static BOOL IsD(wchar_t c) { return c >= L'0' && c <= L'9'; }

static void FmtVer(const wchar_t *raw, wchar_t *out, int n) {
    const wchar_t *v = raw;
    while (*v == L' ') v++;
    if (*v == L'V' || *v == L'v') v++;
    if (!*v) { out[0] = 0; return; }
    swprintf_s(out, n, L"V%s", v);
}

static void GetTag(HWND h, wchar_t *tag, int n) {
    if (IsDlgButtonChecked(h, IDC_CAT_CLI) == BST_CHECKED)
        wcscpy_s(tag, n, L"【客户】");
    else if (IsDlgButtonChecked(h, IDC_SUB_DRAFT) == BST_CHECKED)
        wcscpy_s(tag, n, L"【初稿】");
    else if (IsDlgButtonChecked(h, IDC_SUB_REV) == BST_CHECKED) {
        wchar_t v[32], fv[32];
        GetDlgItemText(h, IDC_VER, v, 32);
        FmtVer(v, fv, 32);
        if (*fv) swprintf_s(tag, n, L"【修订%s】", fv);
        else wcscpy_s(tag, n, L"【修订V1】");
    } else if (IsDlgButtonChecked(h, IDC_SUB_FINAL) == BST_CHECKED)
        wcscpy_s(tag, n, L"【终稿】");
    else tag[0] = 0;
}

static void UpdatePreview(HWND h) {
    if (!gReady) return;
    wchar_t d[16], tag[64], name[MAX_PATH], v[32], fv[32], buf[MAX_PATH * 2];
    GetDlgItemText(h, IDC_DATE, d, 16);
    GetTag(h, tag, 64);
    GetDlgItemText(h, IDC_FNAME, name, MAX_PATH);
    GetDlgItemText(h, IDC_VER, v, 32);
    FmtVer(v, fv, 32);
    if (*fv)
        swprintf_s(buf, _countof(buf), L"%s_%s_%s_%s%s", d, tag, name, fv, gExt);
    else
        swprintf_s(buf, _countof(buf), L"%s_%s_%s%s", d, tag, name, gExt);
    SetDlgItemText(h, IDC_PREVIEW, buf);
}

static BOOL Validate(HWND h) {
    SetDlgItemText(h, IDC_ERR, L"");
    wchar_t d[16]; GetDlgItemText(h, IDC_DATE, d, 16);
    if (!*d) { SetDlgItemText(h, IDC_ERR, L"日期不能为空"); return FALSE; }
    if (wcslen(d) != 8) { SetDlgItemText(h, IDC_ERR, L"日期格式错误，请输入8位数字（如 20260418）"); return FALSE; }
    for (int i = 0; i < 8; i++)
        if (!IsD(d[i])) { SetDlgItemText(h, IDC_ERR, L"日期格式错误，请输入8位数字"); return FALSE; }
    int y = _wtoi(d), mo = _wtoi(d + 4), dd = _wtoi(d + 6);
    if (y < 1900 || y > 2100 || mo < 1 || mo > 12 || dd < 1 || dd > 31) {
        SetDlgItemText(h, IDC_ERR, L"日期范围错误"); return FALSE;
    }
    wchar_t name[MAX_PATH]; GetDlgItemText(h, IDC_FNAME, name, MAX_PATH);
    if (!*name) { SetDlgItemText(h, IDC_ERR, L"文件名称不能为空"); return FALSE; }
    wchar_t v[32]; GetDlgItemText(h, IDC_VER, v, 32);
    if (*v) {
        const wchar_t *p = v;
        if (*p == L'V' || *p == L'v') p++;
        if (!IsD(*p)) goto badver;
        while (IsD(*p)) p++;
        if (*p == L'.') { p++; if (!IsD(*p)) goto badver; while (IsD(*p)) p++; }
        if (*p) goto badver;
    }
    return TRUE;
badver:
    SetDlgItemText(h, IDC_ERR, L"版本号格式错误，只需输入数字（如 1、1.1）");
    return FALSE;
}

static BOOL TryParse(const wchar_t *nm, wchar_t *date, wchar_t *tag, wchar_t *fn, wchar_t *ver) {
    date[0] = tag[0] = fn[0] = ver[0] = 0;
    size_t len = wcslen(nm);
    if (len < 10) return FALSE;
    for (int i = 0; i < 8; i++) if (!IsD(nm[i])) return FALSE;
    if (nm[8] != L'-' && nm[8] != L'_') return FALSE;
    wcsncpy_s(date, 16, nm, 8);
    const wchar_t *r = nm + 9;
    if (*r != L'【') return FALSE;
    const wchar_t *te = wcschr(r, L'】');
    if (!te) return FALSE;
    size_t tl = te - r + 1;
    wcsncpy_s(tag, 64, r, tl);
    wchar_t tc[64]; wcsncpy_s(tc, 64, r + 1, (size_t)(te - r - 1));
    if (wcscmp(tc, L"客户") && wcscmp(tc, L"初稿") && wcscmp(tc, L"终稿")) {
        if (wcsncmp(tc, L"修订V", 3) == 0 || wcsncmp(tc, L"修订v", 3) == 0) {
            const wchar_t *p = tc + 3;
            while (*p) { if (!IsD(*p) && *p != L'.') return FALSE; p++; }
            if (p == tc + 3) return FALSE;
        } else return FALSE;
    }
    r = te + 1;
    if (!*r || (*r != L'-' && *r != L'_')) return FALSE;
    r++;
    size_t rlen = wcslen(r);
    const wchar_t *vs = NULL;
    for (size_t i = rlen; i > 0; i--) {
        if ((r[i - 1] == L'_' || r[i - 1] == L'-') && (r[i] == L'V' || r[i] == L'v')) {
            const wchar_t *p = r + i + 1;
            BOOL ok = TRUE;
            while (*p) { if (!IsD(*p) && *p != L'.') { ok = FALSE; break; } p++; }
            if (ok && p != r + i + 1) { vs = r + i; break; }
        }
    }
    if (vs) {
        wcsncpy_s(fn, MAX_PATH, r, (size_t)(vs - r));
        wcscpy_s(ver, 32, vs + 1);
    } else {
        wcscpy_s(fn, MAX_PATH, r);
    }
    return *fn != 0;
}

static void UpdateSubVis(HWND h) {
    BOOL law = IsDlgButtonChecked(h, IDC_CAT_LAW) == BST_CHECKED;
    ShowWindow(hSubDraft, law ? SW_SHOW : SW_HIDE);
    ShowWindow(hSubRev, law ? SW_SHOW : SW_HIDE);
    ShowWindow(hSubFinal, law ? SW_SHOW : SW_HIDE);
}

static void UpdateFinVis(HWND h) {
    BOOL show = gLawyer
        && IsDlgButtonChecked(h, IDC_CAT_LAW) == BST_CHECKED
        && IsDlgButtonChecked(h, IDC_SUB_FINAL) != BST_CHECKED;
    ShowWindow(hFinBg, show ? SW_SHOW : SW_HIDE);
    ShowWindow(hFinText, show ? SW_SHOW : SW_HIDE);
    ShowWindow(hFinBtn, show ? SW_SHOW : SW_HIDE);
}

/* ---- Create controls ---- */
static HWND MkLabel(HWND h, const wchar_t *text, int y, HFONT font, COLORREF fg) {
    HWND ctl = CreateWindowExW(0, L"Static", text,
        WS_CHILD | WS_VISIBLE, M, y, CW, LH, h, NULL, gInst, NULL);
    SendMessage(ctl, WM_SETFONT, (WPARAM)font, TRUE);
    return ctl;
}

static HWND MkEdit(HWND h, int id, int y, DWORD extra) {
    HWND ctl = CreateWindowExW(0, L"Edit", L"",
        WS_CHILD | WS_VISIBLE | extra,
        M + CARD_PAD, y, CW - 2 * CARD_PAD, EH, h, (HMENU)(INT_PTR)id, gInst, NULL);
    SendMessage(ctl, WM_SETFONT, (WPARAM)gFont, TRUE);
    return ctl;
}

static HWND MkRadio(HWND h, int id, const wchar_t *text, int x, int y, int w, BOOL first) {
    DWORD style = WS_CHILD | WS_VISIBLE | BS_AUTORADIOBUTTON | (first ? WS_GROUP : 0);
    HWND ctl = CreateWindowExW(0, L"Button", text, style,
        x, y, w, RH, h, (HMENU)(INT_PTR)id, gInst, NULL);
    SendMessage(ctl, WM_SETFONT, (WPARAM)gFont, TRUE);
    return ctl;
}

/* ---- Draw an owner-draw button with rounded corners ---- */
static void DrawRoundButton(DRAWITEMSTRUCT *dis, HBRUSH brNormal, HBRUSH brHover,
                            BOOL isHover, COLORREF textCol, BOOL isBold) {
    RECT rc = dis->rcItem;
    HDC dc = dis->hDC;

    /* Fill background */
    HBRUSH br = isHover ? brHover : brNormal;
    FillRoundRect(dc, rc.left, rc.top, rc.right - rc.left, rc.bottom - rc.top, 8, br);

    /* Draw text */
    SetTextColor(dc, textCol);
    SetBkMode(dc, TRANSPARENT);
    HFONT fnt = isBold ? gFontBtn : gFont;
    HFONT oldF = (HFONT)SelectObject(dc, fnt);

    wchar_t text[64];
    GetWindowTextW(dis->hwndItem, text, 64);
    DrawTextW(dc, text, -1, &rc, DT_CENTER | DT_VCENTER | DT_SINGLELINE);
    SelectObject(dc, oldF);
}

/* ---- Window Proc ---- */
static LRESULT CALLBACK WndProc(HWND h, UINT msg, WPARAM wp, LPARAM lp) {
    switch (msg) {

    case WM_CREATE: {
        /* Title in header (drawn via WM_PAINT) */
        hHeader = CreateWindowExW(0, L"Static", L"法律文件重命名",
            WS_CHILD | WS_VISIBLE, M, 18, CW, 36, h, NULL, gInst, NULL);
        SendMessage(hHeader, WM_SETFONT, (WPARAM)gFontTitle, TRUE);

        /* Subtitle */
        HWND hSub = CreateWindowExW(0, L"Static", L"规范化命名，高效管理法律文档",
            WS_CHILD | WS_VISIBLE, M, 46, CW, 16, h, NULL, gInst, NULL);
        SendMessage(hSub, WM_SETFONT, (WPARAM)gFontS, TRUE);

        /* Finalize bar (hidden by default) */
        hFinBg = CreateWindowExW(0, L"Static", NULL,
            WS_CHILD | SS_OWNERDRAW | SS_NOTIFY,
            M, R_ORIG_L - 40, CW, 34, h, (HMENU)IDC_FIN_BG, gInst, NULL);
        hFinText = CreateWindowExW(0, L"Static", L"检测到律师文件，可一键定稿",
            WS_CHILD, M + 12, R_ORIG_L - 34, 220, LH, h, NULL, gInst, NULL);
        SendMessage(hFinText, WM_SETFONT, (WPARAM)gFontS, TRUE);
        hFinBtn = CreateWindowExW(0, L"Button", L"一键定稿",
            WS_CHILD | BS_OWNERDRAW,
            M + CW - 100, R_ORIG_L - 40, 90, 28, h,
            (HMENU)(INT_PTR)IDC_FINALIZE, gInst, NULL);

        /* Original path (read-only) */
        MkLabel(h, L"原文件", R_ORIG_L, gFontS, COL_TEXT_MUTED);
        MkEdit(h, IDC_ORIG, R_ORIG_E, ES_READONLY);
        SetDlgItemText(h, IDC_ORIG, gPath);

        /* Date */
        MkLabel(h, L"日期  YYYYMMDD", R_DATE_L, gFontS, COL_TEXT_MUTED);
        MkEdit(h, IDC_DATE, R_DATE_E, 0);
        SendMessage(GetDlgItem(h, IDC_DATE), EM_LIMITTEXT, 8, 0);

        /* Category */
        MkLabel(h, L"文件类型", R_CAT_L, gFontS, COL_TEXT_MUTED);
        MkRadio(h, IDC_CAT_CLI, L"客户文件", M + 14, R_CAT_R, 100, TRUE);
        MkRadio(h, IDC_CAT_LAW, L"律师文件", M + 130, R_CAT_R, 100, FALSE);

        /* Sub-type radios */
        hSubDraft = MkRadio(h, IDC_SUB_DRAFT, L"初稿", M + 30, R_SUB_R, 80, TRUE);
        hSubRev   = MkRadio(h, IDC_SUB_REV,   L"修订", M + 130, R_SUB_R, 80, FALSE);
        hSubFinal = MkRadio(h, IDC_SUB_FINAL,  L"终稿", M + 220, R_SUB_R, 80, FALSE);

        /* File name */
        MkLabel(h, L"文件名称", R_NAME_L, gFontS, COL_TEXT_MUTED);
        MkEdit(h, IDC_FNAME, R_NAME_E, 0);

        /* Version */
        MkLabel(h, L"版本号  只需输入数字，如 1、1.1", R_VER_L, gFontS, COL_TEXT_MUTED);
        MkEdit(h, IDC_VER, R_VER_E, 0);
        SendMessage(GetDlgItem(h, IDC_VER), EM_LIMITTEXT, 10, 0);

        /* Preview */
        MkLabel(h, L"预览", R_PREV_L, gFontS, COL_ACCENT);
        HWND hp = CreateWindowExW(0, L"Static", L"",
            WS_CHILD | WS_VISIBLE | SS_CENTER | SS_CENTERIMAGE,
            M, R_PREV_E, CW, R_PREV_H, h, (HMENU)(INT_PTR)IDC_PREVIEW, gInst, NULL);
        SendMessage(hp, WM_SETFONT, (WPARAM)gFontPrev, TRUE);

        /* Error text */
        hErr = CreateWindowExW(0, L"Static", L"",
            WS_CHILD | WS_VISIBLE, M, R_BOTTOM, CW - 200, LH, h,
            (HMENU)(INT_PTR)IDC_ERR, gInst, NULL);
        SendMessage(hErr, WM_SETFONT, (WPARAM)gFontS, TRUE);

        /* Buttons — owner-draw rounded */
        hBtnCancel = CreateWindowExW(0, L"Button", L"取消",
            WS_CHILD | WS_VISIBLE | BS_OWNERDRAW,
            M + CW - 172, R_BOTTOM, 76, 34, h,
            (HMENU)(INT_PTR)IDC_CANCEL, gInst, NULL);

        hBtnOk = CreateWindowExW(0, L"Button", L"确认重命名",
            WS_CHILD | WS_VISIBLE | BS_OWNERDRAW,
            M + CW - 88, R_BOTTOM, 88, 34, h,
            (HMENU)(INT_PTR)IDC_OK, gInst, NULL);

        /* ---- Initialize from parsed filename ---- */
        wchar_t today[16];
        SYSTEMTIME st; GetLocalTime(&st);
        swprintf_s(today, 16, L"%04d%02d%02d", st.wYear, st.wMonth, st.wDay);
        SetDlgItemText(h, IDC_DATE, today);
        SetDlgItemText(h, IDC_FNAME, gName);

        wchar_t date[16], tag[64], fname[MAX_PATH], ver[32];
        if (TryParse(gName, date, tag, fname, ver)) {
            gLawyer = TRUE;
            SetDlgItemText(h, IDC_DATE, date);
            SetDlgItemText(h, IDC_FNAME, fname);
            if (*ver) {
                const wchar_t *vd = ver;
                if (*vd == L'V' || *vd == L'v') vd++;
                SetDlgItemText(h, IDC_VER, vd);
            }
            if (wcscmp(tag, L"【客户】") == 0) {
                CheckRadioButton(h, IDC_CAT_CLI, IDC_CAT_LAW, IDC_CAT_CLI);
            } else {
                CheckRadioButton(h, IDC_CAT_CLI, IDC_CAT_LAW, IDC_CAT_LAW);
                if (wcscmp(tag, L"【初稿】") == 0)
                    CheckRadioButton(h, IDC_SUB_DRAFT, IDC_SUB_FINAL, IDC_SUB_DRAFT);
                else if (wcsstr(tag, L"修订"))
                    CheckRadioButton(h, IDC_SUB_DRAFT, IDC_SUB_FINAL, IDC_SUB_REV);
                else if (wcscmp(tag, L"【终稿】") == 0)
                    CheckRadioButton(h, IDC_SUB_DRAFT, IDC_SUB_FINAL, IDC_SUB_FINAL);
            }
        } else {
            CheckRadioButton(h, IDC_CAT_CLI, IDC_CAT_LAW, IDC_CAT_CLI);
        }

        UpdateSubVis(h);
        UpdateFinVis(h);

        gReady = TRUE;
        UpdatePreview(h);
        return 0;
    }

    case WM_PAINT: {
        PAINTSTRUCT ps;
        HDC dc = BeginPaint(h, &ps);

        RECT rc; GetClientRect(h, &rc);

        /* Background */
        FillRect(dc, &rc, gBrBg);

        /* Header band */
        RECT hdrRc = { 0, 0, rc.right, R_HEADER_H };
        FillRoundRect(dc, 0, 0, rc.right, R_HEADER_H, 0, gBrPrimary);

        /* Accent line under header */
        RECT lineRc = { M, R_HEADER_H - 3, M + 60, R_HEADER_H };
        FillRect(dc, &lineRc, gBrAccent);

        /* Card area behind input fields */
        int cardTop = R_ORIG_L - 8;
        int cardH = R_VER_E + EH + 8 - cardTop;
        FillRoundRect(dc, M - CARD_PAD, cardTop, CW + 2 * CARD_PAD, cardH, CARD_R, gBrCard);
        FrameRoundRect(dc, M - CARD_PAD, cardTop, CW + 2 * CARD_PAD, cardH, CARD_R, gPenCard);

        /* Preview card */
        FillRoundRect(dc, M - 2, R_PREV_E - 4, CW + 4, R_PREV_H + 8, 8, gBrPreview);
        FrameRoundRect(dc, M - 2, R_PREV_E - 4, CW + 4, R_PREV_H + 8, 8, gPenPreview);

        EndPaint(h, &ps);
        return 0;
    }

    case WM_COMMAND:
        switch (LOWORD(wp)) {
        case IDC_CAT_CLI:
        case IDC_CAT_LAW:
            UpdateSubVis(h);
            UpdateFinVis(h);
            UpdatePreview(h);
            break;
        case IDC_SUB_DRAFT:
        case IDC_SUB_REV:
        case IDC_SUB_FINAL:
            UpdateFinVis(h);
            UpdatePreview(h);
            break;
        case IDC_OK: {
            if (!Validate(h)) return 0;
            wchar_t buf[MAX_PATH * 2];
            GetDlgItemText(h, IDC_PREVIEW, buf, _countof(buf));
            wchar_t drive[_MAX_DRIVE], d[_MAX_DIR];
            _wsplitpath_s(gPath, drive, _MAX_DRIVE, d, _MAX_DIR, NULL, 0, NULL, 0);
            wchar_t dirBuf[MAX_PATH];
            swprintf_s(dirBuf, _countof(dirBuf), L"%s%s", drive, d);
            wchar_t newPath[MAX_PATH];
            swprintf_s(newPath, _countof(newPath), L"%s%s", dirBuf, buf);
            if (wcscmp(gPath, newPath) != 0 && GetFileAttributesW(newPath) != INVALID_FILE_ATTRIBUTES) {
                if (MessageBoxW(h, L"文件已存在，是否覆盖？", L"确认",
                        MB_YESNO | MB_ICONWARNING) != IDYES)
                    return 0;
                MoveFileExW(gPath, newPath, MOVEFILE_REPLACE_EXISTING);
            } else {
                MoveFileW(gPath, newPath);
            }
            DWORD err = GetLastError();
            if (err != 0) {
                wchar_t emsg[256];
                FormatMessageW(FORMAT_MESSAGE_FROM_SYSTEM, NULL, err, 0, emsg, 256, NULL);
                wchar_t msg[512];
                swprintf_s(msg, _countof(msg), L"重命名失败：%s", emsg);
                SetDlgItemText(h, IDC_ERR, msg);
                SetLastError(0);
                return 0;
            }
            MessageBoxW(h, buf, L"重命名成功", MB_OK | MB_ICONINFORMATION);
            PostQuitMessage(0);
            return 0;
        }
        case IDC_CANCEL:
            PostQuitMessage(0);
            return 0;
        case IDC_FINALIZE: {
            CheckRadioButton(h, IDC_CAT_CLI, IDC_CAT_LAW, IDC_CAT_LAW);
            CheckRadioButton(h, IDC_SUB_DRAFT, IDC_SUB_FINAL, IDC_SUB_FINAL);
            UpdateSubVis(h);
            UpdateFinVis(h);
            UpdatePreview(h);
            SendMessage(h, WM_COMMAND, IDC_OK, 0);
            return 0;
        }
        default:
            if (HIWORD(wp) == EN_CHANGE) {
                switch (LOWORD(wp)) {
                case IDC_DATE: case IDC_FNAME: case IDC_VER:
                    UpdatePreview(h);
                    break;
                }
            }
            break;
        }
        break;

    case WM_DRAWITEM: {
        DRAWITEMSTRUCT *dis = (DRAWITEMSTRUCT *)lp;

        if (dis->CtlID == IDC_OK) {
            DrawRoundButton(dis, gBrBtnOk, gBrBtnOkH, gHoverOk, COL_TEXT_WHITE, TRUE);
            return TRUE;
        }
        if (dis->CtlID == IDC_CANCEL) {
            DrawRoundButton(dis, gBrBtnCancel, gBrBtnCancelH, gHoverCancel, COL_TEXT_SECONDARY, FALSE);
            return TRUE;
        }
        if (dis->CtlID == IDC_FINALIZE) {
            DrawRoundButton(dis, gBrBtnFin, gBrBtnFinH, gHoverFin, COL_TEXT_WHITE, TRUE);
            return TRUE;
        }
        if (dis->CtlID == IDC_FIN_BG) {
            FillRoundRect(dis->hDC, dis->rcItem.left, dis->rcItem.top,
                dis->rcItem.right - dis->rcItem.left,
                dis->rcItem.bottom - dis->rcItem.top, 8, gBrWarnBg);
            FrameRoundRect(dis->hDC, dis->rcItem.left, dis->rcItem.top,
                dis->rcItem.right - dis->rcItem.left,
                dis->rcItem.bottom - dis->rcItem.top, 8, gPenWarn);
            return TRUE;
        }
        return FALSE;
    }

    case WM_MOUSEMOVE: {
        POINT pt = { LOWORD(lp), HIWORD(lp) };
        RECT rc;

        GetWindowRect(hBtnOk, &rc);
        MapWindowPoints(HWND_DESKTOP, h, (LPPOINT)&rc, 2);
        BOOL hOk = PtInRect(&rc, pt);
        if (hOk != gHoverOk) { gHoverOk = hOk; InvalidateRect(hBtnOk, NULL, TRUE); }

        GetWindowRect(hBtnCancel, &rc);
        MapWindowPoints(HWND_DESKTOP, h, (LPPOINT)&rc, 2);
        BOOL hCancel = PtInRect(&rc, pt);
        if (hCancel != gHoverCancel) { gHoverCancel = hCancel; InvalidateRect(hBtnCancel, NULL, TRUE); }

        if (IsWindowVisible(hFinBtn)) {
            GetWindowRect(hFinBtn, &rc);
            MapWindowPoints(HWND_DESKTOP, h, (LPPOINT)&rc, 2);
            BOOL hFin = PtInRect(&rc, pt);
            if (hFin != gHoverFin) { gHoverFin = hFin; InvalidateRect(hFinBtn, NULL, TRUE); }
        }

        /* Track mouse leave to reset hover */
        TRACKMOUSEEVENT tme = { sizeof(tme), TME_LEAVE, h, 0 };
        TrackMouseEvent(&tme);
        return 0;
    }

    case WM_MOUSELEAVE:
        if (gHoverOk) { gHoverOk = FALSE; InvalidateRect(hBtnOk, NULL, TRUE); }
        if (gHoverCancel) { gHoverCancel = FALSE; InvalidateRect(hBtnCancel, NULL, TRUE); }
        if (gHoverFin) { gHoverFin = FALSE; InvalidateRect(hFinBtn, NULL, TRUE); }
        return 0;

    case WM_CTLCOLORSTATIC: {
        HDC dc = (HDC)wp;
        HWND ctl = (HWND)lp;

        /* Header title & subtitle */
        if (ctl == hHeader) {
            SetTextColor(dc, COL_TEXT_WHITE);
            SetBkMode(dc, TRANSPARENT);
            return (LRESULT)gBrPrimary;
        }
        /* Subtitle */
        if (ctl == GetWindow(h, GW_CHILD) && GetParent(ctl) == h) {
            /* skip, handled below */
        }

        /* Finalize bar */
        if (ctl == hFinText) {
            SetTextColor(dc, COL_WARN_AMBER);
            SetBkMode(dc, TRANSPARENT);
            return (LRESULT)gBrWarnBg;
        }
        if (ctl == hFinBg) {
            return (LRESULT)gBrWarnBg;
        }

        /* Preview */
        if (ctl == GetDlgItem(h, IDC_PREVIEW)) {
            SetTextColor(dc, COL_PREVIEW_TEXT);
            SetBkMode(dc, TRANSPARENT);
            return (LRESULT)gBrPreview;
        }

        /* Error */
        if (ctl == hErr) {
            SetTextColor(dc, COL_ERR);
            SetBkMode(dc, TRANSPARENT);
            return (LRESULT)gBrBg;
        }

        /* Read-only path */
        if (ctl == GetDlgItem(h, IDC_ORIG)) {
            SetTextColor(dc, COL_TEXT_READONLY);
            SetBkMode(dc, TRANSPARENT);
            return (LRESULT)gBrInput;
        }

        /* Default labels */
        SetTextColor(dc, COL_TEXT_SECONDARY);
        SetBkMode(dc, TRANSPARENT);
        return (LRESULT)gBrBg;
    }

    case WM_CTLCOLOREDIT: {
        HDC dc = (HDC)wp;
        SetTextColor(dc, COL_TEXT_PRIMARY);
        SetBkMode(dc, TRANSPARENT);
        return (LRESULT)gBrInput;
    }

    case WM_CTLCOLORBTN: {
        return (LRESULT)gBrBg;
    }

    /* Prevent edit controls from scrolling */
    case WM_VSCROLL:
    case WM_HSCROLL:
        return 0;

    case WM_ERASEBKGND: {
        RECT rc; GetClientRect(h, &rc);
        FillRect((HDC)wp, &rc, gBrBg);
        return TRUE;
    }

    case WM_DESTROY:
        PostQuitMessage(0);
        return 0;
    }

    return DefWindowProcW(h, msg, wp, lp);
}

/* ---- Entry Point ---- */
int WINAPI wWinMain(HINSTANCE hInst, HINSTANCE hPrevInst, LPWSTR cmdLine, int nCmdShow) {
    (void)hPrevInst; (void)nCmdShow;

    if (!cmdLine || !*cmdLine) {
        MessageBoxW(NULL, L"请通过右键菜单启动此程序。", L"提示",
            MB_OK | MB_ICONINFORMATION);
        return 0;
    }

    wchar_t path[MAX_PATH] = {0};
    if (cmdLine[0] == L'"') {
        const wchar_t *end = wcschr(cmdLine + 1, L'"');
        if (end) wcsncpy_s(path, MAX_PATH, cmdLine + 1, (size_t)(end - cmdLine - 1));
    } else {
        wcscpy_s(path, MAX_PATH, cmdLine);
    }
    if (!*path || !PathFileExistsW(path)) {
        MessageBoxW(NULL, L"文件不存在。", L"错误", MB_OK | MB_ICONERROR);
        return 0;
    }

    wcscpy_s(gPath, MAX_PATH, path);
    const wchar_t *fname = PathFindFileNameW(path);
    wcscpy_s(gName, MAX_PATH, fname);
    const wchar_t *dot = wcsrchr(fname, L'.');
    if (dot) wcscpy_s(gExt, 32, dot);
    else gExt[0] = 0;
    if (dot) gName[dot - fname] = 0;

    gInst = hInst;

    /* Fonts */
    gFont = CreateFontW(-14, 0, 0, 0, FW_NORMAL, 0, 0, 0, DEFAULT_CHARSET,
        0, 0, CLEARTYPE_QUALITY, 0, L"Microsoft YaHei UI");
    gFontB = CreateFontW(-14, 0, 0, 0, FW_BOLD, 0, 0, 0, DEFAULT_CHARSET,
        0, 0, CLEARTYPE_QUALITY, 0, L"Microsoft YaHei UI");
    gFontS = CreateFontW(-12, 0, 0, 0, FW_NORMAL, 0, 0, 0, DEFAULT_CHARSET,
        0, 0, CLEARTYPE_QUALITY, 0, L"Microsoft YaHei UI");
    gFontTitle = CreateFontW(-22, 0, 0, 0, FW_BOLD, 0, 0, 0, DEFAULT_CHARSET,
        0, 0, CLEARTYPE_QUALITY, 0, L"Microsoft YaHei UI");
    gFontPrev = CreateFontW(-15, 0, 0, 0, FW_BOLD, 0, 0, 0, DEFAULT_CHARSET,
        0, 0, CLEARTYPE_QUALITY, 0, L"Consolas");
    gFontBtn = CreateFontW(-14, 0, 0, 0, FW_SEMIBOLD, 0, 0, 0, DEFAULT_CHARSET,
        0, 0, CLEARTYPE_QUALITY, 0, L"Microsoft YaHei UI");

    /* Brushes */
    gBrBg       = CreateSolidBrush(COL_BG);
    gBrCard     = CreateSolidBrush(COL_CARD);
    gBrInput    = CreateSolidBrush(COL_INPUT_BG);
    gBrPreview  = CreateSolidBrush(COL_PREVIEW_BG);
    gBrWarnBg   = CreateSolidBrush(COL_WARN_BG);
    gBrPrimary  = CreateSolidBrush(COL_PRIMARY);
    gBrAccent   = CreateSolidBrush(COL_ACCENT);
    gBrSuccess  = CreateSolidBrush(COL_SUCCESS);
    gBrDanger   = CreateSolidBrush(COL_DANGER);
    gBrBtnOk      = CreateSolidBrush(COL_SUCCESS);
    gBrBtnOkH     = CreateSolidBrush(COL_SUCCESS_HOVER);
    gBrBtnCancel  = CreateSolidBrush(COL_CARD);
    gBrBtnCancelH = CreateSolidBrush(COL_INPUT_BG);
    gBrBtnFin     = CreateSolidBrush(COL_WARN_AMBER);
    gBrBtnFinH    = CreateSolidBrush(COL_ACCENT);

    /* Pens */
    gPenCard      = CreatePen(PS_SOLID, 1, COL_CARD_BORDER);
    gPenInput     = CreatePen(PS_SOLID, 1, COL_INPUT_BORDER);
    gPenInputFocus= CreatePen(PS_SOLID, 2, COL_INPUT_FOCUS);
    gPenPreview   = CreatePen(PS_SOLID, 1, COL_PREVIEW_BORDER);
    gPenWarn      = CreatePen(PS_SOLID, 1, COL_WARN_BORDER);

    WNDCLASSEXW wc = {0};
    wc.cbSize        = sizeof(wc);
    wc.lpfnWndProc   = WndProc;
    wc.hInstance      = hInst;
    wc.hCursor        = LoadCursorW(NULL, IDC_ARROW);
    wc.hbrBackground  = gBrBg;
    wc.lpszClassName  = L"LegalFileRenamer";
    RegisterClassExW(&wc);

    /* Calculate actual window rect including title bar & borders */
    RECT rc = { 0, 0, WIN_W, WIN_H };
    AdjustWindowRect(&rc, WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU, FALSE);
    int realW = rc.right - rc.left;
    int realH = rc.bottom - rc.top;

    int sx = GetSystemMetrics(SM_CXSCREEN);
    int sy = GetSystemMetrics(SM_CYSCREEN);
    HWND hwnd = CreateWindowExW(0, L"LegalFileRenamer", L"法律文件重命名",
        WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU,
        (sx - realW) / 2, (sy - realH) / 2, realW, realH,
        NULL, NULL, hInst, NULL);

    ShowWindow(hwnd, SW_SHOW);
    UpdateWindow(hwnd);

    MSG msg;
    while (GetMessageW(&msg, NULL, 0, 0)) {
        if (!IsDialogMessageW(hwnd, &msg)) {
            TranslateMessage(&msg);
            DispatchMessageW(&msg);
        }
    }

    /* Cleanup */
    DeleteObject(gFont);
    DeleteObject(gFontB);
    DeleteObject(gFontS);
    DeleteObject(gFontTitle);
    DeleteObject(gFontPrev);
    DeleteObject(gFontBtn);
    DeleteObject(gBrBg);
    DeleteObject(gBrCard);
    DeleteObject(gBrInput);
    DeleteObject(gBrPreview);
    DeleteObject(gBrWarnBg);
    DeleteObject(gBrPrimary);
    DeleteObject(gBrAccent);
    DeleteObject(gBrSuccess);
    DeleteObject(gBrDanger);
    DeleteObject(gBrBtnOk);
    DeleteObject(gBrBtnOkH);
    DeleteObject(gBrBtnCancel);
    DeleteObject(gBrBtnCancelH);
    DeleteObject(gBrBtnFin);
    DeleteObject(gBrBtnFinH);
    DeleteObject(gPenCard);
    DeleteObject(gPenInput);
    DeleteObject(gPenInputFocus);
    DeleteObject(gPenPreview);
    DeleteObject(gPenWarn);

    return (int)msg.wParam;
}
