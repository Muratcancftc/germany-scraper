export default function SettingsPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Einstellungen</h1>
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Kontoinformationen</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">E-Mail</label>
            <input type="email" className="input-field" placeholder="E-Mail" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Passwort</label>
            <input type="password" className="input-field" placeholder="Neues Passwort" />
          </div>
          <button className="btn-primary">Speichern</button>
        </div>
      </div>
    </div>
  );
}
