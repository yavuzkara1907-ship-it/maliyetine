# -*- coding: utf-8 -*-
"""Aylik otomasyon workflow'unun tutarlilik testleri.

NEDEN VAR: 2026-07-27'de bulundu - `sss/` sayfasi veriye gore
degistigi halde workflow'un `git add` listesinde YOKTU. 5 Agustos
olcumunde her sey guncellenirken o sayfa 26 Temmuz verisinde donup
kalacakti. Kimse fark etmezdi: sayfa canlida 200 doner, sadece
rakamlari bayattir. Bu projede daha once yasanan "bayat sayfa"
hatasinin ayni sinifi.

Workflow YILDA 24 KEZ calisiyor ve arada kimse bakmiyor; sessiz
bir eksik aylarca surebilir. Bu yuzden tutarliligi test kilitliyor.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

BASE = Path(__file__).parent
WORKFLOW = BASE.parent / ".github" / "workflows" / "aylik-veri-guncelleme.yml"


def _metin() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def _git_add_yollari() -> list[str]:
    m = re.search(r"git add ([^\n]*(?:\n\s+[^\n]*)*?)\n\s+if ", _metin(), re.S)
    assert m, "git add blogu bulunamadi"
    return [x for x in m.group(1).replace("\\", "").split()
            if x and not x.startswith("#")]


def _uretilen_kok_yollar() -> set[str]:
    """Boru hattinin SITE_KOK altinda yazdigi kok yollar."""
    yollar = set()
    for f in BASE.glob("*.py"):
        if f.name.startswith("test_"):
            continue
        for m in re.finditer(r'SITE_KOK\s*/\s*"([^"]+)"', f.read_text(encoding="utf-8")):
            yollar.add(m.group(1))
    return yollar


class WorkflowTesti(unittest.TestCase):

    def test_uretilen_her_yol_commit_ediliyor(self):
        """EN KRITIK: bir sayfa uretilip commit edilmezse canlida
        SESSIZCE bayatlar - hata vermez, sadece eski rakami gosterir."""
        add = _git_add_yollari()
        for yol in sorted(_uretilen_kok_yollar()):
            if not (BASE.parent / yol).exists():
                continue  # henuz uretilmemis (ör. opsiyonel cikti)
            kapsanmis = any(
                yol == p or yol.startswith(p.rstrip("/") + "/") for p in add
            )
            self.assertTrue(
                kapsanmis,
                f"'{yol}' uretiliyor ama workflow'un git add listesinde yok - "
                f"canlida bayat kalir.",
            )

    def test_calistirilan_her_script_diskte_var(self):
        for ad in set(re.findall(r"python (\w+\.py)", _metin())):
            self.assertTrue((BASE / ad).exists(), f"workflow {ad} cagiriyor ama dosya yok")

    def test_her_vertikal_workflow_dongusunde(self):
        """Yeni vertikal eklenip buraya yazilmazsa o vertikal hic
        guncellenmez (okul eklenirken gecmis.py'de yasanan hata)."""
        import sayfa_uret as su
        m = re.search(r"for vertikal in ([^;]+); do", _metin())
        self.assertIsNotNone(m, "vertikal dongusu bulunamadi")
        dongudeki = set(m.group(1).split())
        self.assertEqual(dongudeki, set(su.VERTIKALLER),
                         "workflow dongusu ile VERTIKALLER ayrismis")

    def test_bagimliliklar_requirements_icinde(self):
        """Workflow `pip install -r requirements.txt` yapiyor; kodun
        import ettigi ucuncu taraf paket orada yoksa adim coker."""
        req = (BASE / "requirements.txt").read_text(encoding="utf-8").lower()
        for paket in ("requests", "beautifulsoup4", "pyyaml", "protego", "playwright"):
            self.assertIn(paket, req, f"{paket} requirements.txt'te yok")
        # sosyal.py X gonderimi icin kullaniyor
        if "requests_oauthlib" in (BASE / "sosyal.py").read_text(encoding="utf-8"):
            self.assertIn("requests-oauthlib", req)

    def test_cron_ayin_5i_ve_20si(self):
        """Olcum sikligi zaman serisinin temeli - bir ay atlanirsa
        seride kalici delik olusur."""
        self.assertIn('cron: "0 6 5,20 * *"', _metin())

    def test_indexnow_yalnizca_degisiklik_varsa(self):
        """Bos bildirim gondermek arama motorlarinda guven kaybettirir."""
        self.assertIn("steps.commit.outputs.degisti == 'true'", _metin())
    def test_hicbir_test_sessizce_calismiyor_durumda_degil(self):
        """BUGUN IKI KEZ YASANDI: dosya sonuna eklenen bir test
        `if __name__ == "__main__":` blogunun ICINE dustu; hic
        calismadigi halde suite YESIL gorunuyordu.

        DIKKAT - ilk yazimda bu test YANLIS POZITIF veriyordu:
        `if __name__` satirindan SONRA gelen her `def test_`i hata
        sayiyordu. Oysa arada yeni bir `class` varsa (test_asistan.py'de
        oldugu gibi) sinif modul seviyesinde tanimlanir ve testler
        NORMAL calisir - 12/12 kosarak dogrulandi.

        Gercek hata bicimi: `def test_` ile son `class` satiri arasinda
        bir `if __name__` var. Yani test hicbir sinifa ait degil.
        """
        for dosya in sorted(BASE.glob("test_*.py")):
            satirlar = dosya.read_text(encoding="utf-8").splitlines()
            son_class = -1
            son_main = -1
            for i, satir in enumerate(satirlar):
                if satir.startswith("class "):
                    son_class = i
                elif satir.startswith("if __name__ =="):
                    son_main = i
                elif re.match(r"\s+def test_", satir) and son_main > son_class:
                    self.fail(
                        f"{dosya.name}:{i+1} — bu test hicbir sinifa ait degil "
                        f"(`if __name__` blogunun icinde kalmis), hic "
                        f"calismiyor: {satir.strip()[:60]}")

    def test_her_test_dosyasi_en_az_bir_test_kosuyor(self):
        """Bir dosya import hatasi yuzunden sessizce bos kalabilir."""
        import unittest as ut
        for dosya in sorted(BASE.glob("test_*.py")):
            paket = ut.defaultTestLoader.loadTestsFromName(dosya.stem)
            self.assertGreater(paket.countTestCases(), 0,
                               f"{dosya.name}: hic test kosmuyor")


if __name__ == "__main__":
    unittest.main()
