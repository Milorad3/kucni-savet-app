import { useState } from "react";
import { useRouter } from "next/router";
import Link from "next/link";
import { api, saveToken } from "../lib/api";

const ACCOUNT_TYPES = [
  {
    id: "admin",
    title: "Predsednik/predsednica saveta",
    description: "Vodim jednu zgradu - zakazujem sastanke i glasanja za svoju zgradu.",
  },
  {
    id: "company",
    title: "Firma - upravnik zgrada",
    description: "Moja firma profesionalno upravlja sa vise zgrada odjednom.",
  },
  {
    id: "resident",
    title: "Stanar/vlasnik stana",
    description: "Predsednik ili firma ce me dodati kao vlasnika stana u svojoj zgradi.",
  },
];

export default function Register() {
  const [accountType, setAccountType] = useState("admin");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const router = useRouter();

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    try {
      await api.register({ full_name: fullName, email, password });
      const res = await api.login({ email, password });
      saveToken(res.access_token);

      // Kljucni deo - odmah nakon registracije vodi na PRAVI sledeci korak,
      // umesto na prazan dashboard koji zbunjuje ("zasto pise stanar?").
      if (accountType === "admin") {
        router.push("/buildings/new");
      } else if (accountType === "company") {
        router.push("/companies/new");
      } else {
        router.push("/dashboard");
      }
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="container">
      <h1>Dobrodošli</h1>
      <p>Recite nam ukratko ko ste, da vas odvedemo na pravo mesto:</p>

      <div className="role-select">
        {ACCOUNT_TYPES.map((type) => (
          <label
            key={type.id}
            className={`role-option ${accountType === type.id ? "selected" : ""}`}
          >
            <input
              type="radio"
              name="accountType"
              value={type.id}
              checked={accountType === type.id}
              onChange={() => setAccountType(type.id)}
            />
            <div>
              <strong>{type.title}</strong>
              <p>{type.description}</p>
            </div>
          </label>
        ))}
      </div>

      <div className="card">
        <form onSubmit={handleSubmit}>
          {error && <div className="error">{error}</div>}
          <input
            placeholder="Ime i prezime"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            required
          />
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Lozinka (min. 8 karaktera)"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
          />
          <button type="submit">
            {accountType === "admin" && "Registruj se i kreiraj zgradu"}
            {accountType === "company" && "Registruj se i kreiraj firmu"}
            {accountType === "resident" && "Registruj se"}
          </button>
        </form>
      </div>
      <p>
        Vec imate nalog? <Link href="/login">Prijavite se</Link>
      </p>
    </div>
  );
}
