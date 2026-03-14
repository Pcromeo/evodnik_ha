# eVodník pro Home Assistant

Integrace umožňuje přihlásit se do VTS **https://servis.evodnik.cz** a načítat stav zařízení eVodník (průtoky, režimy, ventil, apod.).
Součástí je i **kumulativní vodoměr** vhodný pro **Energy Dashboard** v Home Assistantu.

## Poděkování a původ projektu

Tento projekt vychází z původní integrace **eVodník** od autora **AidenShaw2020**.

Původní repozitář:
- https://github.com/AidenShaw2020/evodnik_cloud_ha

Tato větev / fork rozšiřuje původní projekt o další ovládací prvky a úpravy použitelnosti v Home Assistantu.

## Co přidává tato upravená verze

Oproti původní integraci tato verze nově přidává zejména:

- možnost **otevřít vodu**
- možnost **zavřít vodu**
- přepnutí na **automatický režim**
- základní ovládání režimu **Dovolená** přímo z Home Assistantu
  - nastavení **od**
  - nastavení **do**
  - nastavení **limitu litrů**
  - tlačítko pro aktivaci režimu
- doplnění dalších entit tak, aby byly lépe použitelné přímo v zařízení v Home Assistantu

## Stav projektu

Tato verze vznikla jako moje **první veřejně sdílená úprava Home Assistant integrace**, takže ji ber prosím jako funkční, ale stále postupně laděný projekt.

Aktuálně je ověřené zejména:

- čtení dat z eVodníka
- stav ventilu
- základní režimy ovládání
- režim Dovolená

Některé pokročilejší funkce eVodníka zatím nemusí být v Home Assistantu kompletně pokryté nebo mohou být dostupné pouze přes webový portál eVodník.

## Hlášení chyb a návrhy

Když narazíš na problém, budu rád za nahlášení přes Issues v repozitáři.
Stejně tak uvítám návrhy na vylepšení, protože integrace se dál vyvíjí.

Prosím počítej s tím, že:
- neručím za 100% bezchybnost
- některé funkce mohou záviset na změnách na straně cloudového rozhraní eVodník
- některé režimy mohou vyžadovat další ladění

## 📦 Instalace

### Varianta A – přes HACS (doporučeno)

1. Otevřete **HACS → Integrations**.
2. Klikněte na **⋯ (tři tečky) → Custom repositories**.
3. Přidejte adresu repozitáře a zvolte **Category: Integration**.  
   - (https://github.com/Pcromeo/evodnik_ha/)
4. V HACS vyhledejte **eVodník** → **Install**.
5. **Restartujte** Home Assistant.
6. Přejděte do **Settings → Devices & Services → Add Integration** a vyhledejte **eVodník**.

> Pokud používáte HACS poprvé, sledujte oficiální postup instalace HACS: https://hacs.xyz/docs/setup/download/

### Varianta B – ruční instalace

1. Stáhněte release ZIP a rozbalte složku `evodnik` do: `config/custom_components/`
2. **Restartujte** Home Assistant.
3. Přejděte do **Settings → Devices & Services → Add Integration** a vyhledejte **eVodník**.

## Licence

Tento projekt je šířen pod licencí **GNU GPL v3**, stejně jako původní projekt, ze kterého vychází.
