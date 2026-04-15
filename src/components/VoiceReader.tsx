import { useState, useEffect, useRef } from "react";

interface VoiceReaderProps {
  transcript: string;
}

export default function VoiceReader({ transcript }: VoiceReaderProps) {
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [selectedVoice, setSelectedVoice] = useState<string>("");
  const [rate, setRate] = useState(1.0);
  const [pitch, setPitch] = useState(1.0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  useEffect(() => {
    const loadVoices = () => {
      const v = window.speechSynthesis.getVoices();
      if (v.length > 0) {
        setVoices(v);
        const preferred = v.find(
          (x) =>
            x.lang.startsWith("en") &&
            (x.name.includes("Google") || x.name.includes("Natural") || x.name.includes("Neural"))
        );
        setSelectedVoice(preferred?.name || v[0]?.name || "");
      }
    };
    loadVoices();
    window.speechSynthesis.onvoiceschanged = loadVoices;
    return () => { window.speechSynthesis.cancel(); };
  }, []);

  const speak = () => {
    if (!transcript) return;
    window.speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(transcript);
    const voice = voices.find((v) => v.name === selectedVoice);
    if (voice) utter.voice = voice;
    utter.rate = rate;
    utter.pitch = pitch;
    utter.onstart = () => { setIsPlaying(true); setIsPaused(false); };
    utter.onend = () => { setIsPlaying(false); setIsPaused(false); };
    utter.onerror = () => { setIsPlaying(false); setIsPaused(false); };
    utteranceRef.current = utter;
    window.speechSynthesis.speak(utter);
  };

  const pause = () => {
    window.speechSynthesis.pause();
    setIsPaused(true);
  };

  const resume = () => {
    window.speechSynthesis.resume();
    setIsPaused(false);
  };

  const stop = () => {
    window.speechSynthesis.cancel();
    setIsPlaying(false);
    setIsPaused(false);
  };

  if (!transcript) return null;

  const englishVoices = voices.filter((v) => v.lang.startsWith("en"));

  return (
    <div style={{
      border: "1px solid var(--color-border, #e2e8f0)",
      borderRadius: "12px",
      padding: "20px",
      marginTop: "16px",
      background: "var(--color-surface, #f8fafc)"
    }}>
      <p style={{ margin: "0 0 16px", fontWeight: 600, fontSize: "15px" }}>
        AI voice reader
      </p>

      {/* Voice selector */}
      <div style={{ marginBottom: "12px" }}>
        <label style={{ fontSize: "13px", color: "#64748b", display: "block", marginBottom: "4px" }}>
          Voice
        </label>
        <select
          value={selectedVoice}
          onChange={(e) => setSelectedVoice(e.target.value)}
          style={{
            width: "100%", padding: "8px 10px", borderRadius: "8px",
            border: "1px solid #cbd5e1", fontSize: "14px",
            background: "white", cursor: "pointer"
          }}
        >
          {englishVoices.map((v) => (
            <option key={v.name} value={v.name}>
              {v.name} ({v.lang})
            </option>
          ))}
        </select>
      </div>

      {/* Speed slider */}
      <div style={{ marginBottom: "10px" }}>
        <label style={{ fontSize: "13px", color: "#64748b", display: "flex", justifyContent: "space-between" }}>
          <span>Speed</span><span>{rate.toFixed(1)}x</span>
        </label>
        <input type="range" min="0.5" max="2" step="0.1" value={rate}
          onChange={(e) => setRate(parseFloat(e.target.value))}
          style={{ width: "100%", marginTop: "4px" }} />
      </div>

      {/* Pitch slider */}
      <div style={{ marginBottom: "16px" }}>
        <label style={{ fontSize: "13px", color: "#64748b", display: "flex", justifyContent: "space-between" }}>
          <span>Pitch</span><span>{pitch.toFixed(1)}</span>
        </label>
        <input type="range" min="0.5" max="2" step="0.1" value={pitch}
          onChange={(e) => setPitch(parseFloat(e.target.value))}
          style={{ width: "100%", marginTop: "4px" }} />
      </div>

      {/* Controls */}
      <div style={{ display: "flex", gap: "10px" }}>
        {!isPlaying ? (
          <button onClick={speak} style={{
            padding: "10px 24px", borderRadius: "8px", border: "none",
            background: "#3b82f6", color: "white", fontWeight: 600,
            fontSize: "14px", cursor: "pointer"
          }}>
            Play
          </button>
        ) : (
          <>
            {!isPaused ? (
              <button onClick={pause} style={{
                padding: "10px 20px", borderRadius: "8px", border: "none",
                background: "#f59e0b", color: "white", fontWeight: 600,
                fontSize: "14px", cursor: "pointer"
              }}>
                Pause
              </button>
            ) : (
              <button onClick={resume} style={{
                padding: "10px 20px", borderRadius: "8px", border: "none",
                background: "#10b981", color: "white", fontWeight: 600,
                fontSize: "14px", cursor: "pointer"
              }}>
                Resume
              </button>
            )}
            <button onClick={stop} style={{
              padding: "10px 20px", borderRadius: "8px", border: "none",
              background: "#ef4444", color: "white", fontWeight: 600,
              fontSize: "14px", cursor: "pointer"
            }}>
              Stop
            </button>
          </>
        )}
      </div>

      {isPlaying && !isPaused && (
        <p style={{ marginTop: "12px", fontSize: "13px", color: "#64748b" }}>
          Reading cleaned transcript aloud...
        </p>
      )}
    </div>
  );
}
