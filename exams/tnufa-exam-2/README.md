# מבחן תנופה לדוגמה (נובמבר 2026) — הכנה לכיתה ט׳ (`exams/tnufa-exam-2`)

מבחן חדש ונפרד מהמבחן הקיים בשורש הריפו. מקור האמת של המבחן הזה: [`SOURCE_OF_TRUTH.md`](SOURCE_OF_TRUTH.md).
שום קובץ מחוץ לתיקייה הזו לא משתנה בבנייה.

## הפקה — פקודה אחת

```powershell
Set-Location C:\Users\yaniv\Documents\GitHub\Tnufa
python exams/tnufa-exam-2/build.py
```

הפקודה מריצה את בדיקות ה־QA האוטומטיות, ואז מפיקה:

| תוצר | נתיב | ציבורי? |
|---|---|---|
| חוברת תלמיד (A4, 17 עמודים: שער, הוראות, 12 עמודי שאלות, 2 דפי טיוטה, עמוד סיום) | `public/STUDENT.pdf` | כן |
| אתר/קורא: שער + עמודי החוברת בגלילה, מעבר בחוברת, הדפסה והורדה | `public/index.html` | כן |
| מניפסט (hash של ה־PDF, חלוקת שאלות לעמודים) | `public/manifest.json` | כן |
| חוברת מורה: מפת המבחן, כללי בדיקה, פתרון מלא + מחוון + טעויות לכל שאלה | `private/TEACHER.pdf`, `private/teacher.html` | **לא** — `private/` לא נכנס ל־git |
| Blueprint (תוכנית נעולה מול ביצוע) | `BLUEPRINT.json` | כן |

אפשרויות: `--student` / `--teacher` (רק צד אחד), `--check` (QA בלי דפדפן), `--preview N` (שאלה N לבד על דף A4 → `build/preview-qN.png`),
`--snapshots` (כל עמוד ל־PNG: `qa/pages/` לתלמיד, `private/pages/` למורה), `--update-hashes` (קבלת שינוי בשאלות כבסיס רגרסיה חדש).

דרישות: Python 3.12, `playwright` (Chromium מותקן), `pymupdf`. הגופנים (Heebo, Rubik) נטענים מ־Google Fonts בזמן הרינדור.

## עריכת שאלה אחת

כל שאלה היא קובץ אחד: `src/exam2/questions/qNN.py`. בקובץ, באותו מקום: הנוסח לתלמיד (`html`), השרטוט (`figure()`),
הנתונים, התשובה, הפתרון המלא, דרכים חלופיות, המחוון (`rubric`), טעויות צפויות, כלל טעות נגררת, ומטא־נתונים
(תחום, רמת חשיבה לכל סעיף, זמן, ייצוגים, מקוריות, נגישות). פונקציית `check()` מחשבת מחדש את כל ערכי המפתח — הבנייה נכשלת אם ערך שגוי.

1. ערכו את `qNN.py`.
2. `python exams/tnufa-exam-2/build.py --preview NN` ובדקו את `build/preview-qNN.png`.
3. `python exams/tnufa-exam-2/build.py` — הבדיקות מדווחות אילו שאלות השתנו מול `tests/question-hashes.json` (רגרסיה לשאלות שלא נגעתם בהן).
4. כשמרוצים: `--update-hashes`.

העימוד דטרמיניסטי: כל שאלה נמדדת בכרומיום, ומוכנסת לעמוד שלם (שאלה לא מתפצלת). מקום פנוי בעמוד מגדיל את חלונות הכתיבה.

## מבנה

```
build.py                 פקודת ההפקה
src/exam2/model.py       Question / Part (מודל הפריט)
src/exam2/questions/     q01.py … q17.py
src/exam2/svg.py         עזרי שרטוט וקטורי (מישור צירים, זוויות, סימוני שוויון/הקבלה)
src/exam2/html.py        עזרי סימון (מתמטיקה ב־LTR, שברים, שורש, אפשרויות, חלונות כתיבה)
src/exam2/booklet.py     CSS, שער, הוראות, טיוטה, סיום, חוברת מורה
src/exam2/render.py      עימוד, PDF, קורא web, תצוגה מקדימה
src/exam2/checks.py      QA אוטומטי + hash רגרסיה לכל שאלה
src/exam2/blueprint.py   היעדים הנעולים (תחומים, רמות חשיבה, אוריינות, זמן)
tests/question-hashes.json  בסיס הרגרסיה
tools/sha_guard.py       הוכחת אי־שינוי המבחן המקורי (SHA-256 לפני/אחרי)
tools/publish.py         פרסום public/ לריפו אתר ה־GitHub Pages (תוצר בנייה בלבד)
qa/                      דוח QA, צילומי עמודים, רשומת ה־SHA של המקור
public/                  תוצרי התלמיד (מוכנים לפריסה כאתר סטטי נפרד)
private/                 תוצרי המורה (לא ב־git)
```

## קישור חיצוני נפרד — GitHub Pages

האתר החי: **https://yanivmizrachiy.github.io/tnufa-exam-2/** (ריפו `yanivmizrachiy/tnufa-exam-2`, ציבורי, Pages מ־`main`).
הריפו הזה הוא תוצר בנייה בלבד — אין לערוך בו ידנית. מקור האמת היחיד הוא התיקייה הזו.

עדכון האתר אחרי שינוי במבחן:

```powershell
Set-Location C:\Users\yaniv\Documents\GitHub\Tnufa
python exams/tnufa-exam-2/build.py
python exams/tnufa-exam-2/tools/publish.py
```

`publish.py` מרוקן את ה־clone של אתר הפרסום (`..\tnufa-exam-2`, או `SITE_DIR`), מעתיק אליו את `public/` + `SOURCE.json` (ה־commit במקור), דוחף ענף `publish-<תאריך>-<sha>` ופותח PR; מיזוג ה־PR מעדכן את האתר. `tnufa.vercel.app` והמבחן המקורי אינם נוגעים בכך.
