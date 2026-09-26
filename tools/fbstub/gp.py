"""Test helper (0.4.5_11): «Nuovo gioco»/«Hardcore» now ask which game for Uomo roccia; pick «Mangiaroccia" when the chooser is up (no-op otherwise, e.g. Algidone)."""


def pick_maze(p):
    p.evaluate("(()=>{const b=document.querySelector('[data-rg=maze]');if(b)b.click();0})()")
