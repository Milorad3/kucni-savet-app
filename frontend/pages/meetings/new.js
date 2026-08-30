import { useState } from "react";
import { useRouter } from "next/router";
import { api } from "../../lib/api";

export default function NewMeeting() {
  const router = useRouter();
  const { building_id } = router.query; // prisutno kad dolazi sa company dashboard-a

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [scheduledAt, setScheduledAt] = useState("");
  const [agendaItems, setAgendaItems] = useState([{ title: "", description: "" }]);
  const [error, setError] = useState("");

  function updateAgendaItem(idx, field, value) {
    const updated = [...agendaItems];
    updated[idx][field] = value;
    setAgendaItems(updated);
  }

  function addAgendaItem() {
    setAgendaItems([...agendaItems, { title: "", description: "" }]);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    try {
      const meeting = await api.createMeeting({
        title,
        description,
        scheduled_at: new Date(scheduledAt).toISOString(),
        agenda_items: agendaItems.filter((a) => a.title.trim() !== ""),
        building_id: building_id || undefined,
      });
      router.push(`/meetings/${meeting.id}`);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="container">
      <h1>Novi sastanak</h1>
      <div className="card">
        <form onSubmit={handleSubmit}>
          {error && <div className="error">{error}</div>}
          <input placeholder="Naslov sastanka" value={title} onChange={(e) => setTitle(e.target.value)} required />
          <textarea placeholder="Opis (opciono)" value={description} onChange={(e) => setDescription(e.target.value)} />
          <input
            type="datetime-local"
            value={scheduledAt}
            onChange={(e) => setScheduledAt(e.target.value)}
            required
          />

          <h3>Dnevni red</h3>
          {agendaItems.map((item, idx) => (
            <input
              key={idx}
              placeholder={`Tačka ${idx + 1}`}
              value={item.title}
              onChange={(e) => updateAgendaItem(idx, "title", e.target.value)}
            />
          ))}
          <button type="button" className="secondary" onClick={addAgendaItem}>
            + Dodaj tačku
          </button>
          <br /><br />
          <button type="submit">Sačuvaj sastanak</button>
        </form>
      </div>
    </div>
  );
}
