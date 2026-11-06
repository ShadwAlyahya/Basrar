import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, Lock, Mail } from 'lucide-react';
import logoImg from '../basrar-logo.jpg';

export default function Login() {
    const navigate = useNavigate();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');

    const handleLogin = (e) => {
        e.preventDefault();
        // Dynamic navigation to upload step
        navigate('/upload');
    };

    return (
        <div style={{ minHeight: '100vh', backgroundColor: '#EAE2D6', display: 'flex', justifyContent: 'center', alignItems: 'center', fontFamily: 'system-ui, sans-serif' }}>
            <div style={{ backgroundColor: '#0F172A', padding: '40px', borderRadius: '24px', width: '100%', maxWidth: '420px', border: '1px solid #D4AF3740', boxShadow: '0 20px 50px rgba(0,0,0,0.3)', color: '#FFF' }}>
                <div style={{ textAlign: 'center', marginBottom: '28px' }}>
                    <div style={{ padding: '8px 16px', borderRadius: '12px', backgroundColor: '#EAE2D6', border: '1px solid #D4AF37', display: 'inline-block', marginBottom: '16px' }}>
                        <img src={logoImg} alt="Basrar AI" style={{ height: '48px', objectFit: 'contain' }} />
                    </div>
                    <h2 style={{ fontSize: '22px', fontWeight: 'bold', margin: '0 0 6px 0', color: '#F8FAFC' }}>Welcome Back</h2>
                    <p style={{ fontSize: '13px', color: '#94A3B8', margin: 0 }}>Basrar Executive AI Intelligence</p>
                </div>

                <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
                    <div>
                        <label style={{ display: 'block', fontSize: '12px', color: '#CBD5E1', marginBottom: '6px', fontWeight: '600' }}>Email Address</label>
                        <div style={{ position: 'relative' }}>
                            <Mail style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', width: '16px', height: '16px', color: '#64748B' }} />
                            <input
                                type="email"
                                required
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="name@company.com"
                                style={{ width: '100%', padding: '12px 12px 12px 38px', borderRadius: '10px', border: '1px solid #334155', backgroundColor: '#1E293B', color: '#FFF', fontSize: '14px', outline: 'none', boxSizing: 'border-box' }}
                            />
                        </div>
                    </div>

                    <div>
                        <label style={{ display: 'block', fontSize: '12px', color: '#CBD5E1', marginBottom: '6px', fontWeight: '600' }}>Password</label>
                        <div style={{ position: 'relative' }}>
                            <Lock style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', width: '16px', height: '16px', color: '#64748B' }} />
                            <input
                                type="password"
                                required
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="••••••••"
                                style={{ width: '100%', padding: '12px 12px 12px 38px', borderRadius: '10px', border: '1px solid #334155', backgroundColor: '#1E293B', color: '#FFF', fontSize: '14px', outline: 'none', boxSizing: 'border-box' }}
                            />
                        </div>
                    </div>

                    <button
                        type="submit"
                        style={{ width: '100%', padding: '12px', borderRadius: '10px', border: 'none', backgroundColor: '#3B82F6', color: '#FFF', fontWeight: '600', fontSize: '14px', cursor: 'pointer', marginTop: '10px', boxShadow: '0 4px 14px rgba(59,130,246,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
                    >
                        <Sparkles style={{ width: '16px', height: '16px' }} /> Sign In to Dashboard
                    </button>
                </form>
            </div>
        </div>
    );
}