import { useState } from "react";
import { LockKeyhole, Save, Trash2 } from "lucide-react";
import {
  clearAstrologyProfile,
  DEFAULT_ASTROLOGY_PROFILE,
  getAstrologyApiBaseUrl,
  loadAstrologyProfile,
  loadSavedAstrologyProfile,
  saveAstrologyProfile,
  type AstrologyProfile,
  type BirthTimeConfidence
} from "../astrology/astrologyApi";

export default function AstroProfileSettings() {
  const [profile, setProfile] = useState<AstrologyProfile>(() => loadAstrologyProfile());
  const [hasOverride, setHasOverride] = useState(() => Boolean(loadSavedAstrologyProfile()));
  const [saved, setSaved] = useState(false);

  function updateProfile<K extends keyof AstrologyProfile>(key: K, value: AstrologyProfile[K]) {
    setSaved(false);
    setProfile((current) => ({ ...current, [key]: value }));
  }

  function handleSave() {
    saveAstrologyProfile({
      ...profile,
      id: profile.id || "local-profile",
      localTime: profile.localTime?.trim() || null
    });
    setHasOverride(true);
    setSaved(true);
  }

  function handleClear() {
    clearAstrologyProfile();
    setProfile(DEFAULT_ASTROLOGY_PROFILE);
    setHasOverride(false);
    setSaved(false);
  }

  return (
    <section className="data-card">
      <div className="card-title-row">
        <LockKeyhole />
        <h2>Astro Profile</h2>
      </div>
      <p>
        The dashboard defaults to the hardcoded personal profile. A saved override stays in this
        browser's local storage and is sent only to the configured local astrology API at{" "}
        <code>{getAstrologyApiBaseUrl()}</code>.
      </p>
      <p className={hasOverride ? "status-good" : "status-muted"}>
        {hasOverride ? "Using saved local override." : "Using hardcoded personal default."}
      </p>
      <div className="form-grid">
        <label className="field-label">
          Display name
          <input value={profile.displayName} onChange={(event) => updateProfile("displayName", event.target.value)} />
        </label>
        <label className="field-label">
          Birth date
          <input type="date" value={profile.localDate} onChange={(event) => updateProfile("localDate", event.target.value)} />
        </label>
        <label className="field-label">
          Birth time
          <input
            type="time"
            value={profile.localTime ?? ""}
            onChange={(event) => updateProfile("localTime", event.target.value)}
          />
        </label>
        <label className="field-label">
          Birth time confidence
          <select
            value={profile.birthTimeConfidence}
            onChange={(event) => updateProfile("birthTimeConfidence", event.target.value as BirthTimeConfidence)}
          >
            <option value="UNKNOWN">Unknown</option>
            <option value="APPROXIMATE">Approximate</option>
            <option value="EXACT_RECALLED">Exact recalled</option>
            <option value="EXACT_RECORD">Exact record</option>
          </select>
        </label>
        <label className="field-label">
          Location
          <input value={profile.locationName} onChange={(event) => updateProfile("locationName", event.target.value)} />
        </label>
        <label className="field-label">
          Time zone
          <input value={profile.timeZoneId} onChange={(event) => updateProfile("timeZoneId", event.target.value)} />
        </label>
      </div>
      <div className="button-row">
        <button className="primary-action" type="button" onClick={handleSave}>
          <Save size={18} />
          Save Local Profile
        </button>
        <button className="secondary-action secondary-action--danger" type="button" onClick={handleClear}>
          <Trash2 size={18} />
          Clear
        </button>
        {saved ? <span className="status-pill status-pill--good">Saved</span> : null}
      </div>
    </section>
  );
}
