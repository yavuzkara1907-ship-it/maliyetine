# -*- coding: utf-8 -*-
"""Fiyat verisinin neyi olctugunu tanimlayan ortak sozlesme.

Bir rakamin para birimi kadar olcum birimi de verinin parcasidir. Kategori
medyani, tuketim miktari normalize edilmeden aylik gidere donusturulemez.
"""

PAKET_FIYATI_KALEMLERI = frozenset({
    "bebek-bezi",
    "cis-pedi",
    "kedi-kumu",
    "kedi-mamasi",
    "kopek-mamasi",
})

KISI_BASI_FIYAT_KALEMLERI = frozenset({
    "salon-kokteyl",
    "salon-yemekli",
    "yemek-ikram",
})


def olcum_turu(kalem_id: str) -> str:
    if kalem_id in PAKET_FIYATI_KALEMLERI:
        return "paket_fiyati"
    if kalem_id in KISI_BASI_FIYAT_KALEMLERI:
        return "kisi_basi_fiyat"
    return "kalem_fiyati"


def kaynak_adi(kalem_id: str, ad: str) -> str:
    """Eski snapshot etiketini degistirmeden yayin ciktisini duzeltir."""
    eski_sonek = " (aylık)"
    if kalem_id in PAKET_FIYATI_KALEMLERI and ad.endswith(eski_sonek):
        return ad[:-len(eski_sonek)] + " (paket fiyatı)"
    return ad
