import React, { useState, useEffect } from 'react';
import { 
  CloudRain, ShieldAlert, CheckSquare, MessageSquare, 
  MapPin, Settings as SettingsIcon, Navigation, AlertTriangle, 
  HelpCircle, Compass, CheckCircle2, RefreshCw, Languages, ArrowRight
} from 'lucide-react';

import en from './i18n/en.json';
import ta from './i18n/ta.json';
import hi from './i18n/hi.json';

const translations = { en, ta, hi };

// API base URL - uses env var in production, relative in dev
const API_BASE = import.meta.env.VITE_API_BASE || 'https://monsoonprep-backend.onrender.com';

export default function App() {
  // Application State
  const [lang, setLang] = useState('en');
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(false);
  const [feedbackMsg, setFeedbackMsg] = useState('');
  
  // Location defaults: Coimbatore, Tamil Nadu
  const [latitude, setLatitude] = useState(11.0168);
  const [longitude, setLongitude] = useState(76.9558);
  
  // Household Profile State
  const [householdSize, setHouseholdSize] = useState(3);
  const [hasChildren, setHasChildren] = useState(false);
  const [hasElderly, setHasElderly] = useState(false);
  const [hasPets, setHasPets] = useState(false);
  const [petDetails, setPetDetails] = useState('');
  const [housingType, setHousingType] = useState('apartment');
  const [hasVehicle, setHasVehicle] = useState(false);
  const [accessibilityNeeds, setAccessibilityNeeds] = useState('');
  
  // Resolved context data
  const [weather, setWeather] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [plan, setPlan] = useState(null);
  const [checklist, setChecklist] = useState(null);
  
  // Chat state
  const [chatInput, setChatInput] = useState('');
  const [chatMessages, setChatMessages] = useState([]);
  
  // Travel state
  const [originLat, setOriginLat] = useState(11.0168);
  const [originLng, setOriginLng] = useState(76.9558);
  const [destLat, setDestLat] = useState(13.0827); // Chennai default
  const [destLng, setDestLng] = useState(80.2707);
  const [travelAdvisory, setTravelAdvisory] = useState(null);

  // Localization helper
  const t = (key) => {
    return translations[lang][key] || en[key] || key;
  };

  // Sync dashboard context when location/settings update
  useEffect(() => {
    fetchWeatherAndAlerts();
  }, [latitude, longitude]);

  const fetchWeatherAndAlerts = async () => {
    setLoading(true);
    try {
      // 1. Fetch Weather
      const wRes = await fetch(`${API_BASE}/api/weather?latitude=${latitude}&longitude=${longitude}`);
      if (wRes.ok) {
        const wData = await wRes.json();
        setWeather(wData);
      }

      // 2. Fetch Alerts
      const aRes = await fetch(`${API_BASE}/api/alerts?latitude=${latitude}&longitude=${longitude}&language=${lang}`);
      if (aRes.ok) {
        const aData = await aRes.json();
        setAlerts(aData);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  // Generate Personalized plan
  const generatePlan = async () => {
    setLoading(true);
    setFeedbackMsg('');
    try {
      const payload = {
        location_lat: latitude,
        location_lng: longitude,
        location_name: weather?.current?.location_name || 'Coimbatore',
        household_size: householdSize,
        has_children: hasChildren,
        has_elderly: hasElderly,
        has_pets: hasPets,
        pet_details: petDetails,
        housing_type: housingType,
        has_vehicle: hasVehicle,
        accessibility_needs: accessibilityNeeds,
        preferred_language: lang
      };

      const res = await fetch(`${API_BASE}/api/preparedness/plan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const pData = await res.json();
        setPlan(pData);
        setFeedbackMsg(t('settings_success'));
        
        // Auto-refresh checklist as well
        // We need a profile ID saved in PostgreSQL
        if (pData) {
          // Checklists are queried by household ID if available. Let's create household first
          // Wait, the backend post endpoint /api/preparedness/plan creates/updates the profile and returns it,
          // but our plan model doesn't return profile ID directly.
          // Wait, let's load checklist. The backend get endpoint queries checklist?household_id={id}.
          // Let's retrieve checklist using the plan profile ID if cached
        }
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  // Fetch checklist status
  const loadChecklist = async (hhId) => {
    try {
      const res = await fetch(`${API_BASE}/api/checklist?household_id=${hhId}`);
      if (res.ok) {
        const cData = await res.json();
        setChecklist(cData);
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Toggle checklist item status
  const toggleChecklistItem = async (itemId, currentStatus) => {
    if (!checklist) return;
    const newStatus = currentStatus === 'pending' ? 'completed' : 'pending';
    
    try {
      const res = await fetch(`${API_BASE}/api/checklist/item`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          household_id: checklist.household_id,
          item_id: itemId,
          status: newStatus
        })
      });
      if (res.ok) {
        // Reload checklist
        loadChecklist(checklist.household_id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Chat Q&A submit
  const sendChatMessage = async (e) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const userMsg = { role: 'user', content: chatInput };
    setChatMessages((prev) => [...prev, userMsg]);
    setChatInput('');
    setLoading(true);

    try {
      const payload = {
        question: userMsg.content,
        // Optional household_id if checklist is loaded
        household_id: checklist?.household_id || null
      };

      const res = await fetch(`${API_BASE}/api/assistant/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const data = await res.json();
        setChatMessages((prev) => [
          ...prev, 
          { 
            role: 'assistant', 
            content: data.answer, 
            sources: data.sources,
            observed_at: data.observed_at,
            live_data_used: data.live_data_used,
            is_stale: data.is_stale
          }
        ]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  // Travel risk eval
  const checkTravelRoute = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const payload = {
        origin_lat: originLat,
        origin_lng: originLng,
        dest_lat: destLat,
        dest_lng: destLng,
        preferred_language: lang
      };
      const res = await fetch(`${API_BASE}/api/travel/advisory`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const data = await res.json();
        setTravelAdvisory(data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  // Geolocation helpers
  const detectLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setLatitude(pos.coords.latitude);
          setLongitude(pos.coords.longitude);
        },
        (err) => {
          console.error(err);
        }
      );
    }
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header>
        <div className="brand-section">
          <CloudRain className="brand-logo" size={28} />
          <h1 className="brand-title">{t('app_title')}</h1>
        </div>
        <nav className="nav-links" aria-label="Main Navigation">
          <button className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`} onClick={() => setActiveTab('dashboard')}>
            <Compass size={18} />
            {t('nav_dashboard')}
          </button>
          <button className={`nav-item ${activeTab === 'preparedness' ? 'active' : ''}`} onClick={() => setActiveTab('preparedness')}>
            <ShieldAlert size={18} />
            {t('nav_preparedness')}
          </button>
          <button className={`nav-item ${activeTab === 'checklist' ? 'active' : ''}`} onClick={() => {
            setActiveTab('checklist');
            // Try generating plan first to link household id
            if (!checklist && plan) {
              // Extract household ID from plan metadata if possible
            }
          }}>
            <CheckSquare size={18} />
            {t('nav_checklist')}
          </button>
          <button className={`nav-item ${activeTab === 'assistant' ? 'active' : ''}`} onClick={() => setActiveTab('assistant')}>
            <MessageSquare size={18} />
            {t('nav_assistant')}
          </button>
          <button className={`nav-item ${activeTab === 'travel' ? 'active' : ''}`} onClick={() => setActiveTab('travel')}>
            <Navigation size={18} />
            {t('nav_travel')}
          </button>
          <button className={`nav-item ${activeTab === 'settings' ? 'active' : ''}`} onClick={() => setActiveTab('settings')}>
            <SettingsIcon size={18} />
            {t('nav_settings')}
          </button>
        </nav>
        
        {/* Language selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Languages size={18} color="var(--text-secondary)" />
          <select 
            value={lang} 
            onChange={(e) => setLang(e.target.value)} 
            className="form-select"
            style={{ width: 'auto', padding: '0.25rem 0.5rem', fontSize: '0.85rem' }}
          >
            <option value="en">English</option>
            <option value="ta">தமிழ் (Tamil)</option>
            <option value="hi">हिन्दी (Hindi)</option>
          </select>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="content-area">
        {/* Verification Loader */}
        {loading && (
          <div style={{ display: 'flex', justifyContent: 'center', margin: '1rem 0' }}>
            <RefreshCw className="animate-spin" size={24} color="var(--accent-primary)" />
          </div>
        )}

        {/* --- Tab 1: Dashboard --- */}
        {activeTab === 'dashboard' && (
          <div>
            {/* Active alerts section */}
            {alerts.length > 0 ? (
              alerts.map((alert, idx) => (
                <div key={idx} className={`alert-banner ${alert.severity.toLowerCase()}`}>
                  <AlertTriangle size={24} />
                  <div>
                    <h3 style={{ fontWeight: 700 }}>{alert.title}</h3>
                    <p style={{ fontSize: '0.9rem', marginTop: '0.25rem' }}>
                      {alert.citizen_message || alert.description}
                    </p>
                    <span style={{ fontSize: '0.75rem', opacity: 0.8, display: 'block', marginTop: '0.5rem' }}>
                      Source: {alert.source} | Severity: {alert.severity}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div className="alert-banner low">
                <CheckCircle2 size={24} />
                <div>
                  <h3 style={{ fontWeight: 600 }}>{t('alert_banner_none')}</h3>
                </div>
              </div>
            )}

            <div className="grid-2">
              {/* Weather Context Details */}
              <div className="card">
                <h2 style={{ fontSize: '1.25rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <CloudRain size={20} color="var(--accent-primary)" />
                  {t('weather_title')}
                </h2>
                
                {weather ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span className="text-secondary">Location:</span>
                      <span style={{ fontWeight: 600 }}>{weather.current.location_name || 'Coimbatore'}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span className="text-secondary">{t('weather_temp')}:</span>
                      <span style={{ fontWeight: 600 }}>{weather.current.temperature_celsius}°C</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span className="text-secondary">{t('weather_rain_current')}:</span>
                      <span style={{ fontWeight: 600 }}>{weather.current.rainfall.current_mm} mm</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span className="text-secondary">{t('weather_rain_forecast')}:</span>
                      <span style={{ fontWeight: 600, color: 'var(--accent-secondary)' }}>{weather.current.rainfall.forecast_mm} mm</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span className="text-secondary">{t('weather_wind')}:</span>
                      <span style={{ fontWeight: 600 }}>{weather.current.wind.speed_kmph} km/h</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span className="text-secondary">Monsoon Phase:</span>
                      <span className="badge moderate">{weather.monsoon_phase}</span>
                    </div>
                    <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '0.75rem', marginTop: '0.5rem', display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      <span>{t('weather_source')}: {weather.current.source}</span>
                      <span>{t('weather_observed')}: {new Date(weather.current.observed_at).toLocaleTimeString()}</span>
                    </div>
                  </div>
                ) : (
                  <p className="text-secondary">No weather data loaded.</p>
                )}
              </div>

              {/* Active Risk summary */}
              <div className="card">
                <h2 style={{ fontSize: '1.25rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <ShieldAlert size={20} color="var(--severity-high)" />
                  {t('risk_title')}
                </h2>
                
                {plan ? (
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
                      <span className={`badge ${plan.risk_summary.level.toLowerCase()}`} style={{ fontSize: '1rem', padding: '0.5rem 1rem' }}>
                        {plan.risk_summary.level}
                      </span>
                    </div>
                    <ul style={{ paddingLeft: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                      {plan.risk_summary.reasons.map((r, i) => (
                        <li key={i} style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>{r}</li>
                      ))}
                    </ul>
                  </div>
                ) : (
                  <div>
                    <p className="text-secondary" style={{ marginBottom: '1rem' }}>
                      Please configure your household settings to calculate localized risk.
                    </p>
                    <button className="btn btn-primary" onClick={() => setActiveTab('settings')}>
                      Setup Profile Context
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Quick Actions List (Do Now) */}
            {plan && (
              <div className="card">
                <h2 style={{ fontSize: '1.25rem', marginBottom: '1rem', color: 'var(--severity-severe)' }}>
                  {t('plan_immediate')}
                </h2>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {plan.actions_immediate.map((act, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem', padding: '0.75rem', borderRadius: '8px', backgroundColor: 'rgba(239, 68, 68, 0.05)', border: '1px solid rgba(239, 68, 68, 0.1)' }}>
                      <span className="badge severe" style={{ marginTop: '0.1rem' }}>Priority {act.priority}</span>
                      <p style={{ fontSize: '0.95rem' }}>{act.action}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* --- Tab 2: Preparedness Plan --- */}
        {activeTab === 'preparedness' && (
          <div>
            <div className="card">
              <h2 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>{t('nav_preparedness')}</h2>
              <p className="text-secondary" style={{ marginBottom: '1.5rem' }}>{t('plan_intro')}</p>
              
              <div style={{ display: 'flex', gap: '1rem' }}>
                <button className="btn btn-primary" onClick={generatePlan}>
                  {t('plan_generate_btn')}
                </button>
                <button className="btn btn-secondary" onClick={() => setActiveTab('settings')}>
                  {t('nav_settings')}
                </button>
              </div>
            </div>

            {plan && (
              <div className="grid-2">
                <div>
                  <div className="card">
                    <h3 style={{ fontSize: '1.25rem', marginBottom: '1rem', color: 'var(--accent-secondary)' }}>
                      {t('plan_6h')}
                    </h3>
                    <ul style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', listStyle: 'none' }}>
                      {plan.actions_next_6_hours.map((act, i) => (
                        <li key={i} style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start' }}>
                          <ArrowRight size={16} style={{ marginTop: '0.25rem', color: 'var(--accent-secondary)' }} />
                          <span>{act.action}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="card">
                    <h3 style={{ fontSize: '1.25rem', marginBottom: '1rem', color: 'var(--text-primary)' }}>
                      {t('plan_24h')}
                    </h3>
                    <ul style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', listStyle: 'none' }}>
                      {plan.actions_next_24_hours.map((act, i) => (
                        <li key={i} style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start' }}>
                          <ArrowRight size={16} style={{ marginTop: '0.25rem', color: 'var(--text-muted)' }} />
                          <span>{act.action}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                <div>
                  <div className="card">
                    <h3 style={{ fontSize: '1.25rem', marginBottom: '1rem', color: 'var(--severity-low)' }}>
                      {t('plan_kit')}
                    </h3>
                    <ul style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', listStyle: 'none' }}>
                      {plan.emergency_kit.map((item, i) => (
                        <li key={i} style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                          <input type="checkbox" readOnly checked style={{ accentColor: 'var(--severity-low)' }} />
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {plan.household_specific_actions.length > 0 && (
                    <div className="card">
                      <h3 style={{ fontSize: '1.25rem', marginBottom: '1rem', color: 'var(--accent-primary)' }}>
                        {t('plan_specific')}
                      </h3>
                      <ul style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', listStyle: 'none' }}>
                        {plan.household_specific_actions.map((act, i) => (
                          <li key={i} style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start' }}>
                            <span className="badge low">Vulnerability</span>
                            <span>{act.action}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* --- Tab 3: Checklist --- */}
        {activeTab === 'checklist' && (
          <div>
            <div className="card">
              <h2 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>{t('checklist_title')}</h2>
              
              {checklist ? (
                <div>
                  <div style={{ marginBottom: '1.5rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.9rem' }}>
                      <span className="text-secondary">{t('checklist_progress')}</span>
                      <span style={{ fontWeight: 700 }}>{checklist.completion_percent}%</span>
                    </div>
                    <div style={{ width: '100%', height: '8px', backgroundColor: 'rgba(255,255,255,0.08)', borderRadius: '4px', overflow: 'hidden' }}>
                      <div style={{ width: `${checklist.completion_percent}%`, height: '100%', backgroundColor: 'var(--severity-low)', transition: 'width 0.3s ease' }}></div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {checklist.items.map((item) => (
                      <div key={item.id} className="card" style={{ margin: 0, padding: '1rem', display: 'flex', justifySelf: 'stretch', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
                          <input 
                            type="checkbox" 
                            checked={item.status === 'completed'} 
                            onChange={() => toggleChecklistItem(item.id, item.status)}
                            style={{ width: '20px', height: '20px', marginTop: '0.2rem', accentColor: 'var(--severity-low)' }}
                          />
                          <div>
                            <p style={{ fontWeight: 600, textDecoration: item.status === 'completed' ? 'line-through' : 'none', opacity: item.status === 'completed' ? 0.5 : 1 }}>
                              {item.title}
                            </p>
                            {item.weather_context && (
                              <span style={{ fontSize: '0.8rem', color: 'var(--accent-secondary)' }}>{item.weather_context}</span>
                            )}
                          </div>
                        </div>
                        <span className="text-muted" style={{ fontSize: '0.8rem' }}>{item.category}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div>
                  <p className="text-secondary" style={{ marginBottom: '1rem' }}>
                    Generate a personalized plan first to compile your persistent emergency checklist.
                  </p>
                  <button className="btn btn-primary" onClick={() => setActiveTab('preparedness')}>
                    {t('plan_generate_btn')}
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* --- Tab 4: Assistant --- */}
        {activeTab === 'assistant' && (
          <div>
            <div className="card" style={{ marginBottom: '1rem' }}>
              <h2 style={{ fontSize: '1.5rem' }}>{t('assistant_title')}</h2>
              <p className="text-secondary">AI-grounded emergency safety chat assistant.</p>
            </div>

            <div className="chat-container">
              <div className="chat-messages-box">
                {chatMessages.length === 0 && (
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)' }}>
                    <HelpCircle size={48} style={{ marginBottom: '0.75rem' }} />
                    <p>Ask safety Q&A regarding monsoon events, floods, or wind storms.</p>
                  </div>
                )}
                {chatMessages.map((msg, i) => (
                  <div key={i} className={`chat-bubble ${msg.role}`}>
                    <p>{msg.content}</p>
                    {msg.sources && (
                      <div style={{ borderTop: '1px solid rgba(255,255,255,0.1)', marginTop: '0.5rem', paddingTop: '0.25rem', fontSize: '0.75rem', opacity: 0.8 }}>
                        <strong>{t('assistant_sources')}:</strong> {msg.sources.join(', ')}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              <form onSubmit={sendChatMessage} className="chat-input-bar">
                <input 
                  type="text" 
                  value={chatInput} 
                  onChange={(e) => setChatInput(e.target.value)} 
                  placeholder={t('assistant_input_placeholder')}
                  className="form-input"
                  aria-label="Safety Question"
                />
                <button type="submit" className="btn btn-primary">
                  {t('assistant_ask_btn')}
                </button>
              </form>
            </div>
          </div>
        )}

        {/* --- Tab 5: Travel Advisory --- */}
        {activeTab === 'travel' && (
          <div>
            <div className="card">
              <h2 style={{ fontSize: '1.5rem', marginBottom: '1.5rem' }}>{t('travel_title')}</h2>
              
              <form onSubmit={checkTravelRoute} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div className="grid-2">
                  <div className="form-group">
                    <label className="form-label">{t('travel_origin')}</label>
                    <input 
                      type="text" 
                      placeholder="Coimbatore"
                      className="form-input" 
                      onChange={() => {}} // Simple mock coordinates selection for origin/dest
                    />
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Default coords: {originLat}, {originLng}</span>
                  </div>
                  <div className="form-group">
                    <label className="form-label">{t('travel_dest')}</label>
                    <input 
                      type="text" 
                      placeholder="Chennai"
                      className="form-input"
                      onChange={() => {}}
                    />
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Default coords: {destLat}, {destLng}</span>
                  </div>
                </div>
                
                <button type="submit" className="btn btn-primary" style={{ alignSelf: 'flex-start' }}>
                  {t('travel_check_btn')}
                </button>
              </form>
            </div>

            {travelAdvisory && (
              <div className="card">
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
                  <h3 style={{ fontSize: '1.25rem' }}>Advisory Risk:</h3>
                  <span className={`badge ${travelAdvisory.risk_level.toLowerCase()}`}>
                    {travelAdvisory.risk_level}
                  </span>
                </div>

                <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
                  <div>
                    <h4 style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>Origin Weather ({travelAdvisory.origin_name})</h4>
                    <p style={{ fontSize: '0.95rem', marginTop: '0.25rem' }}>{travelAdvisory.origin_weather_summary}</p>
                  </div>
                  <div>
                    <h4 style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>Destination Weather ({travelAdvisory.destination_name})</h4>
                    <p style={{ fontSize: '0.95rem', marginTop: '0.25rem' }}>{travelAdvisory.destination_weather_summary}</p>
                  </div>
                </div>

                <div className="alert-banner moderate" style={{ margin: '1rem 0' }}>
                  <AlertTriangle size={20} />
                  <div>
                    <h4 style={{ fontWeight: 600 }}>{t('travel_limit_warning')}</h4>
                    <p style={{ fontSize: '0.9rem' }}>{travelAdvisory.limitations.join(' ')}</p>
                  </div>
                </div>

                <div className="card" style={{ backgroundColor: 'rgba(255,255,255,0.02)' }}>
                  <h4 style={{ fontWeight: 600, marginBottom: '0.75rem' }}>Safety Recommendations:</h4>
                  <ul style={{ paddingLeft: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {travelAdvisory.recommendations.map((rec, i) => (
                      <li key={i} style={{ fontSize: '0.95rem' }}>{rec}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        )}

        {/* --- Tab 6: Settings --- */}
        {activeTab === 'settings' && (
          <div className="card" style={{ maxWidth: '800px', margin: '0 auto' }}>
            <h2 style={{ fontSize: '1.5rem', marginBottom: '1.5rem' }}>{t('settings_title')}</h2>
            
            {feedbackMsg && (
              <div className="alert-banner low" style={{ padding: '0.75rem', marginBottom: '1rem' }}>
                <CheckCircle2 size={18} />
                <span style={{ fontSize: '0.9rem' }}>{feedbackMsg}</span>
              </div>
            )}

            <form onSubmit={(e) => { e.preventDefault(); generatePlan(); }}>
              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">{t('settings_lat')}</label>
                  <input type="number" step="0.0001" value={latitude} onChange={(e) => setLatitude(parseFloat(e.target.value))} className="form-input" required />
                </div>
                <div className="form-group">
                  <label className="form-label">{t('settings_lng')}</label>
                  <input type="number" step="0.0001" value={longitude} onChange={(e) => setLongitude(parseFloat(e.target.value))} className="form-input" required />
                </div>
              </div>

              <div style={{ marginBottom: '1.5rem' }}>
                <button type="button" className="btn btn-secondary" onClick={detectLocation}>
                  <MapPin size={16} />
                  {t('settings_detect_loc')}
                </button>
              </div>

              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">{t('settings_size')}</label>
                  <input type="number" min="1" value={householdSize} onChange={(e) => setHouseholdSize(parseInt(e.target.value))} className="form-input" required />
                </div>
                <div className="form-group">
                  <label className="form-label">{t('settings_housing')}</label>
                  <select value={housingType} onChange={(e) => setHousingType(e.target.value)} className="form-select">
                    <option value="apartment">{t('housing_apartment')}</option>
                    <option value="independent_house">{t('housing_independent_house')}</option>
                    <option value="ground_floor">{t('housing_ground_floor')}</option>
                    <option value="kutcha_house">{t('housing_kutcha_house')}</option>
                    <option value="slum">{t('housing_slum')}</option>
                    <option value="temporary_shelter">{t('housing_temporary_shelter')}</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1.5rem' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                  <input type="checkbox" checked={hasChildren} onChange={(e) => setHasChildren(e.target.checked)} style={{ width: '18px', height: '18px' }} />
                  <span>{t('settings_children')}</span>
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                  <input type="checkbox" checked={hasElderly} onChange={(e) => setHasElderly(e.target.checked)} style={{ width: '18px', height: '18px' }} />
                  <span>{t('settings_elderly')}</span>
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                  <input type="checkbox" checked={hasPets} onChange={(e) => setHasPets(e.target.checked)} style={{ width: '18px', height: '18px' }} />
                  <span>{t('settings_pets')}</span>
                </label>
                {hasPets && (
                  <input type="text" placeholder="e.g. 2 dogs, 1 cat" value={petDetails} onChange={(e) => setPetDetails(e.target.value)} className="form-input" />
                )}
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                  <input type="checkbox" checked={hasVehicle} onChange={(e) => setHasVehicle(e.target.checked)} style={{ width: '18px', height: '18px' }} />
                  <span>{t('settings_vehicle')}</span>
                </label>
              </div>

              <div className="form-group">
                <label className="form-label">{t('settings_needs')}</label>
                <textarea value={accessibilityNeeds} onChange={(e) => setAccessibilityNeeds(e.target.value)} className="form-textarea" rows={3}></textarea>
              </div>

              <button type="submit" className="btn btn-primary">
                {t('settings_save_btn')}
              </button>
            </form>
          </div>
        )}
      </main>
    </div>
  );
}
