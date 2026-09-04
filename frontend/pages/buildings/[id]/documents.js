import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import Link from "next/link";
import { api, isLoggedIn } from "../../../lib/api";

const CATEGORIES = [
  { id: "faktura", label: "Faktura" },
  { id: "ugovor", label: "Ugovor" },
  { id: "zapisnik", label: "Zapisnik" },
  { id: "ostalo", label: "Ostalo" },
];

export default function BuildingDocuments() {
  const router = useRouter();
  const { id } = router.query;

  const [building, setBuilding] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);
  const [category, setCategory] = useState("ostalo");
  const [file, setFile] = useState(null);
  const [storageDisabled, setStorageDisabled] = useState(false);

  useEffect(() => {
    if (!isLoggedIn()) {
      router.replace("/login");
      return;
    }
    if (!id) return;
    load();
  }, [id]);

  async function load() {
    try {
      const [b, docs] = await Promise.all([api.getBuilding(id), api.listDocuments(id)]);
      setBuilding(b);
      setDocuments(docs);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleUpload(e) {
    e.preventDefault();
    if (!file) return;
    setError("");
    setUploading(true);
    try {
      await api.uploadDocument(id, file, category);
      setFile(null);
      e.target.reset();
      load();
    } catch (err) {
      if (err.message.includes("Skladiste dokumenata nije podeseno")) {
        setStorageDisabled(true);
      }
      setError(err.message);
    } finally {
      setUploading(false);
    }
  }

  async function handleDownload(docId) {
    setError("");
    try {
      const { url } = await api.getDocumentDownloadUrl(docId);
      window.open(url, "_blank");
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="container">
      <h1>Dokumenti{building ? ` — ${building.name}` : ""}</h1>
      <p>Fakture, ugovori i drugi dokumenti zgrade, na jednom mestu.</p>

      {error && <div className="error">{error}</div>}
      {storageDisabled && (
        <div style={{ background: "#fef3c7", color: "#92400e", padding: "10px 12px", borderRadius: 8, marginBottom: 12, fontSize: 14 }}>
          Skladište dokumenata (S3) još nije podešeno na serveru — treba dodati S3_BUCKET_NAME,
          S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY environment varijable na backend servisu.
        </div>
      )}

      <div className="card">
        <form onSubmit={handleUpload}>
          <h3>Otpremi dokument</h3>
          <input type="file" onChange={(e) => setFile(e.target.files[0])} required />
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            style={{ width: "100%", padding: "10px 12px", border: "1px solid #ddd", borderRadius: 8, marginBottom: 10, fontSize: 15 }}
          >
            {CATEGORIES.map((c) => (
              <option key={c.id} value={c.id}>{c.label}</option>
            ))}
          </select>
          <button type="submit" disabled={uploading}>{uploading ? "Otpremam..." : "Otpremi"}</button>
        </form>
      </div>

      <h3>Postojeći dokumenti ({documents.length})</h3>
      {documents.map((d) => (
        <div key={d.id} className="card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <strong>{d.filename}</strong>
            <p style={{ margin: "4px 0 0 0", fontSize: 13, color: "#666" }}>
              {CATEGORIES.find((c) => c.id === d.category)?.label || d.category} · {new Date(d.uploaded_at).toLocaleDateString("sr-RS")}
            </p>
          </div>
          <button style={{ width: "auto" }} onClick={() => handleDownload(d.id)}>Preuzmi</button>
        </div>
      ))}
      {documents.length === 0 && <p>Još nema otpremljenih dokumenata.</p>}

      <Link href="/dashboard">
        <button className="secondary">← Nazad</button>
      </Link>
    </div>
  );
}
