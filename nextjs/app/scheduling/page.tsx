"use client";

import { useEffect, useState } from "react";
import { AppointmentRecord } from "@/types/schedule";

function isoDate(date: Date) {
  return date.toISOString().slice(0, 10);
}

export default function SchedulingPage() {
  const [appointments, setAppointments] = useState<AppointmentRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [date, setDate] = useState<string>(isoDate(new Date()));
  const [windowMinutes, setWindowMinutes] = useState<number>(60);

  useEffect(() => {
    setLoading(true);
    fetch(`/api/schedules?date=${date}`)
      .then((res) => res.json())
      .then((data) => {
        setAppointments(data.appointments ?? []);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [date]);

  const upcoming = appointments.filter((appt) => {
    const apptTime = new Date(appt.appointment_date).getTime();
    const now = Date.now();
    return apptTime >= now && apptTime <= now + windowMinutes * 60 * 1000;
  });

  return (
    <main style={{ padding: "1.5rem", maxWidth: 960, margin: "0 auto" }}>
      <h1>🟡 Upcoming Appointments</h1>
      <div style={{ display: "flex", gap: "1rem", alignItems: "center", marginBottom: "1rem" }}>
        <label>
          Date:
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            style={{ marginLeft: "0.5rem" }}
          />
        </label>
        <label>
          Window (minutes):
          <input
            type="range"
            min={15}
            max={240}
            step={15}
            value={windowMinutes}
            onChange={(e) => setWindowMinutes(Number(e.target.value))}
            style={{ marginLeft: "0.5rem", width: "200px" }}
          />
          <strong>{windowMinutes}</strong>
        </label>
      </div>

      {loading ? (
        <p>Loading appointments…</p>
      ) : upcoming.length === 0 ? (
        <p>✅ No upcoming appointments in the next {windowMinutes} minutes.</p>
      ) : (
        <div style={{ display: "grid", gap: "1rem" }}>
          <p><strong>{upcoming.length}</strong> upcoming appointment(s)</p>
          {upcoming.map((appt) => (
            <article
              key={appt.id}
              style={{
                border: "1px solid #d2d2d8",
                borderRadius: 8,
                padding: "0.85rem",
                background: "white",
              }}
            >
              <p><strong>{appt.patient_name || "Unknown patient"}</strong> - {appt.doctor || "No doctor"}</p>
              <p>{new Date(appt.appointment_date).toLocaleString()}</p>
              <p>Status: {appt.status || "unknown"}</p>
              <p>{appt.notes}</p>
            </article>
          ))}
        </div>
      )}
    </main>
  );
}
