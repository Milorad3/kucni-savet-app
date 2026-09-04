# Kućni Savet - Aplikacija

Full-stack aplikacija za online sastanke i glasanje kućnog saveta.

## Struktura projekta

```
kucni-savet-app/
├── backend/          # FastAPI (Python) - REST API
├── frontend/         # Next.js (React) - web/mobilni interfejs
├── infra/            # Terraform za AWS (opciono, ako ne koristis Render)
├── docker-compose.yml # Za lokalno testiranje
└── render.yaml        # Za deploy na Render.com
```

## Pokretanje lokalno (za testiranje na svom računaru)

Potreban ti je instaliran Docker.

```bash
docker-compose up --build
```

Zatim otvori:
- Frontend: http://localhost:3000
- Backend API dokumentacija (automatski generisana): http://localhost:8000/docs

## Deploy na Render.com (preporučeno za start)

1. Napravi GitHub repozitorijum i push-uj ovaj kod
2. Idi na render.com → New → Blueprint
3. Poveži GitHub repo - Render će sam pročitati `render.yaml` i kreirati:
   - PostgreSQL bazu
   - Backend web servis
   - Frontend web servis
4. Sačekaj da se build završi (5-10 minuta)
5. Gotovo - dobijaš URL-ove tipa `kucni-savet-frontend.onrender.com`

**Napomena:** besplatan Render plan "uspava" servis posle 15 min neaktivnosti (prvi zahtev posle toga je spor ~30s). Za produkciju, pređi na "Starter" plan (~7$/mesec po servisu).

## Deploy na AWS (za veći obim/skalabilnost)

Terraform kod je u `infra/aws-terraform-main.tf` - pogledaj prethodno objašnjenje u chatu za detalje. Zahteva Docker image u ECR pre pokretanja.

## Test nalog (posle registracije)

1. Registruj se preko `/register`
2. Kreiraj zgradu preko dugmeta na dashboard-u (postaješ admin/predsednik)
3. Dodaj stanove preko API-ja (`POST /buildings/{id}/apartments`) - trenutno nema UI za ovo, može se dodati
4. Kreiraj sastanak, aktiviraj glasanje, glasaj kao vlasnik stana

## Šta nedostaje za produkciju (sledeći koraci)

- ✅ ~~UI za dodavanje stanova~~ — gotovo (`/buildings/[id]/apartments`)
- ✅ ~~Generisanje PDF zapisnika~~ — gotovo (dugme na stranici sastanka)
- ✅ ~~Email notifikacije~~ — gotovo, ALI zahteva SMTP podešavanje (vidi ispod)
- ✅ ~~Upload dokumenata~~ — gotovo, ALI zahteva S3 podešavanje (vidi ispod)
- Alembic migracije baze (umesto auto-create tabela)
- Testovi (unit/integration)

## Podešavanje email notifikacija (opciono)

Bez ovoga, aplikacija radi normalno, samo ne šalje email pozive na glasanje.

Na Render → `kucni-savet-backend` → Environment, dodaj:
- `SMTP_HOST` (npr. `smtp.gmail.com`)
- `SMTP_PORT` (obično `587`)
- `SMTP_USER` (tvoj email)
- `SMTP_PASSWORD` (za Gmail: mora biti "App Password", ne obična lozinka — Google nalog → Security → App Passwords)
- `FROM_EMAIL` (email koji se prikazuje kao pošiljalac)
- `FRONTEND_URL` (npr. `https://kucni-savet-frontend.onrender.com` — da link u email-u radi)

Alternativa Gmail-u: SendGrid, Resend, Mailgun — svi imaju SMTP pristup sa sličnim podešavanjem.

## Podešavanje upload dokumenata (opciono)

Bez ovoga, dugme za upload postoji ali javlja jasnu grešku da skladište nije podešeno.

Na Render → `kucni-savet-backend` → Environment, dodaj:
- `S3_BUCKET_NAME`
- `S3_REGION` (npr. `eu-central-1`)
- `S3_ACCESS_KEY_ID`
- `S3_SECRET_ACCESS_KEY`
- `S3_ENDPOINT_URL` — OSTAVI PRAZNO za AWS S3. Popuni samo ako koristiš Cloudflare R2 ili Backblaze B2 (jeftinije alternative, S3-kompatibilne)

Najjeftinija opcija za mali obim: **Cloudflare R2** (nema naplate za download saobraćaj, za razliku od AWS S3).
