# Skin coverage

Matrice fotogramma x costume, generata da questa build (`tools/fbstub/test_skin_coverage.py`), non scritta a mano: rigenerarla ad ogni chunk che tocca un fotogramma, una posa o un costume (CLAUDE.md §6 regola 11).

Legenda: **ok** = il costume ha quel fotogramma · **manca** = fotogramma reale del foglio (F4a) senza arte per questo costume · **na** = il costume dichiara di non averne bisogno (`SKINS.<id>.na`) · **procedurale — da convertire** = posa disegnata dal codice (es. l'icona mangia procedurale di Uomo roccia), non ancora un fotogramma: nessun costume puo' toccarla oggi. Il Cinghiale di Algidone era in questa categoria fino a F4c (0.4_10): ora ha 6 fotogrammi reali (riga «Cinghiale»).

Build: 0.4.5

## Uomo roccia

| Fotogramma | Riga | Cappello GEKA SNC |
|---|---|---|
| `f0` | Lato | ok |
| `f1` | Lato | ok |
| `f2` | Lato | ok |
| `e0` | Mangia (lato) | ok |
| `e1` | Mangia (lato) | ok |
| `fd0` | Su | ok |
| `fd1` | Su | ok |
| `fd2` | Su | ok |
| `fu0` | Giù | ok |
| `fu3` | Giù | ok |
| `ref_eat_su` | Riferimenti (Mangia su (icona roccia, solo codice)) | procedurale — da convertire |
| `ref_eat_giu` | Riferimenti (Mangia giù (icona roccia, solo codice)) | procedurale — da convertire |

## Algidone

| Fotogramma | Riga | Costume BK |
|---|---|---|
| `al_st` | Lato (fermo + cammina) | ok |
| `al_w0` | Lato (fermo + cammina) | ok |
| `al_w1` | Lato (fermo + cammina) | ok |
| `al_w2` | Lato (fermo + cammina) | ok |
| `al_w3` | Lato (fermo + cammina) | ok |
| `al_w4` | Lato (fermo + cammina) | ok |
| `al_w5` | Lato (fermo + cammina) | ok |
| `al_w6` | Lato (fermo + cammina) | ok |
| `al_w7` | Lato (fermo + cammina) | ok |
| `al_u0` | Su | ok |
| `al_u1` | Su | ok |
| `al_u2` | Su | ok |
| `al_u3` | Su | ok |
| `al_u4` | Su | ok |
| `al_u5` | Su | ok |
| `al_d_st` | Giù (fermo + cammina) | ok |
| `al_d0` | Giù (fermo + cammina) | ok |
| `al_d1` | Giù (fermo + cammina) | ok |
| `al_d2` | Giù (fermo + cammina) | ok |
| `al_d3` | Giù (fermo + cammina) | ok |
| `al_r0` | Rotola (power-up, solo lato) | ok |
| `al_r1` | Rotola (power-up, solo lato) | ok |
| `al_r2` | Rotola (power-up, solo lato) | ok |
| `al_r3` | Rotola (power-up, solo lato) | ok |
| `al_r4` | Rotola (power-up, solo lato) | ok |
| `al_r5` | Rotola (power-up, solo lato) | ok |
| `al_r6` | Rotola (power-up, solo lato) | ok |
| `alg_idle0` | Ferma Algidone! (lanciatore) | manca |
| `alg_idle1` | Ferma Algidone! (lanciatore) | manca |
| `alg_angry0` | Ferma Algidone! (lanciatore) | manca |
| `alg_angry1` | Ferma Algidone! (lanciatore) | manca |
| `alg_throw0` | Ferma Algidone! (lanciatore) | manca |
| `alg_throw1` | Ferma Algidone! (lanciatore) | manca |
| `alg_throw2` | Ferma Algidone! (lanciatore) | manca |
| `alg_throw3` | Ferma Algidone! (lanciatore) | manca |
| `alg_eat0` | Ferma Algidone! (lanciatore) | manca |
| `alg_eat1` | Ferma Algidone! (lanciatore) | manca |
| `alg_eat2` | Ferma Algidone! (lanciatore) | manca |
| `alg_kick1` | Ferma Algidone! (lanciatore) | manca |
| `alg_kick2` | Ferma Algidone! (lanciatore) | manca |
| `boar_lato0` | Cinghiale | manca |
| `boar_lato1` | Cinghiale | manca |
| `boar_su0` | Cinghiale | manca |
| `boar_su1` | Cinghiale | manca |
| `boar_giu0` | Cinghiale | manca |
| `boar_giu1` | Cinghiale | manca |
