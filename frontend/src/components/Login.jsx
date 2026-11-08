import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Sparkles, Mail, Lock, User, KeyRound, ArrowRight, CheckCircle, AlertCircle } from 'lucide-react';
import logoImg from '../basrar-logo.jpg';

export default function Login() {
    const navigate = useNavigate();
    const [isSignUp, setIsSignUp] = useState(false);
    const [isForgotPassword, setIsForgotPassword] = useState(false);
    const [stepVerify, setStepVerify] = useState(false);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [name, setName] = useState('');
    const [code, setCode] = useState('');
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState(null);
    const [error, setError] = useState(null);

    const lang = localStorage.getItem('basrar_lang') || 'en';

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setMessage(null);

        try {
            if (stepVerify) {
                const res = await axios.post('http://localhost:8000/auth/verify-code', { email, code });
                if (res.data?.access_token) {
                    localStorage.setItem('token', res.data.access_token);
                    localStorage.setItem('user_email', email);
                    localStorage.setItem('is_guest', 'false');
                    navigate('/dashboard');
                }
                setLoading(false);
                return;
            }

            if (isForgotPassword) {
                const res = await axios.post('http://localhost:8000/auth/forgot-password', { email, lang });
                setMessage(res.data.message || 'Password reset instructions sent successfully.');
                setLoading(false);
                return;
            }

            if (isSignUp) {
                const res = await axios.post('http://localhost:8000/auth/register', { username: name, email, password, lang });
                setMessage(res.data.message || 'Verification code sent to your email successfully!');
                setStepVerify(true);
                setLoading(false);
                return;
            }

            const response = await axios.post('http://localhost:8000/auth/login', { email, password });
            if (response.data?.access_token) {
                localStorage.setItem('token', response.data.access_token);
                localStorage.setItem('user_email', email);
                localStorage.setItem('is_guest', 'false');
                navigate('/dashboard');
            }
        } catch (err) {
            console.error("Auth Error:", err);
            setError(err.response?.data?.detail || 'An error occurred while connecting to the server.');
        } finally {
            if (!isSignUp && !isForgotPassword && !stepVerify) setLoading(false);
        }
    };

    const handleContinueAsGuest = () => {
        localStorage.setItem('is_guest', 'true');
        localStorage.removeItem('token');
        navigate('/dashboard');
    };

    return (
        <div style={{
            minHeight: '100vh',
            backgroundColor: '#EAE2D6',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '20px',
            fontFamily: 'system-ui, sans-serif'
        }}>
            <div style={{
                backgroundColor: '#0B132B',
                color: '#FFFFFF',
                padding: '40px',
                borderRadius: '24px',
                width: '100%',
                maxWidth: '460px',
                boxShadow: '0 25px 50px rgba(0,0,0,0.3)',
                border: '1px solid rgba(212, 175, 55, 0.3)',
                textAlign: 'center'
            }}>
                <div style={{
                    width: '210px',
                    height: '75px',
                    margin: '0 auto 24px auto',
                    borderRadius: '14px',
                    overflow: 'hidden',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    backgroundColor: '#EAE2D6',
                    padding: '6px',
                    boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.1)'
                }}>
                    <img src={logoImg} alt="Basrar AI" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
                </div>

                <h1 style={{ fontSize: '24px', fontWeight: 'bold', margin: '0 0 6px 0', color: '#FFFFFF' }}>
                    {stepVerify ? 'Verify Your Email' : 'Welcome to Basrar'}
                </h1>
                <p style={{ fontSize: '13px', color: '#94A3B8', margin: '0 0 28px 0', fontWeight: '500' }}>
                    {stepVerify ? 'Enter the 6-digit code sent to your email' : 'Where Analytics Meets Simplicity'}
                </p>

                {message && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', backgroundColor: 'rgba(16, 185, 129, 0.2)', border: '1px solid #10B981', color: '#34D399', padding: '10px 14px', borderRadius: '10px', marginBottom: '20px', fontSize: '13px', textAlign: 'left' }}>
                        <CheckCircle style={{ width: '16px', height: '16px', flexShrink: 0 }} />
                        <span>{message}</span>
                    </div>
                )}

                {error && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', backgroundColor: 'rgba(239, 68, 68, 0.2)', border: '1px solid #EF4444', color: '#F87171', padding: '10px 14px', borderRadius: '10px', marginBottom: '20px', fontSize: '13px', textAlign: 'left' }}>
                        <AlertCircle style={{ width: '16px', height: '16px', flexShrink: 0 }} />
                        <span>{error}</span>
                    </div>
                )}

                <form onSubmit={handleSubmit} style={{ textAlign: 'left' }}>
                    {stepVerify ? (
                        <div style={{ marginBottom: '16px' }}>
                            <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: '#CBD5E1', marginBottom: '6px' }}>Verification Code</label>
                            <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                                <KeyRound style={{ position: 'absolute', left: '14px', width: '16px', height: '16px', color: '#64748B' }} />
                                <input
                                    type="text"
                                    required
                                    maxLength="6"
                                    placeholder="123456"
                                    value={code}
                                    onChange={(e) => setCode(e.target.value)}
                                    style={{ width: '100%', padding: '12px 14px 12px 42px', borderRadius: '10px', border: '1px solid #1E293B', backgroundColor: '#0F172A', color: '#FFF', fontSize: '16px', letterSpacing: '4px', outline: 'none' }}
                                />
                            </div>
                        </div>
                    ) : (
                        <>
                            {isSignUp && (
                                <div style={{ marginBottom: '16px' }}>
                                    <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: '#CBD5E1', marginBottom: '6px' }}>Full Name</label>
                                    <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                                        <User style={{ position: 'absolute', left: '14px', width: '16px', height: '16px', color: '#64748B' }} />
                                        <input
                                            type="text"
                                            required
                                            placeholder="Shadw Alyahya"
                                            value={name}
                                            onChange={(e) => setName(e.target.value)}
                                            style={{ width: '100%', padding: '12px 14px 12px 42px', borderRadius: '10px', border: '1px solid #1E293B', backgroundColor: '#0F172A', color: '#FFF', fontSize: '14px', outline: 'none' }}
                                        />
                                    </div>
                                </div>
                            )}

                            <div style={{ marginBottom: '16px' }}>
                                <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: '#CBD5E1', marginBottom: '6px' }}>Email Address</label>
                                <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                                    <Mail style={{ position: 'absolute', left: '14px', width: '16px', height: '16px', color: '#64748B' }} />
                                    <input
                                        type="email"
                                        required
                                        placeholder="name@example.com"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        style={{ width: '100%', padding: '12px 14px 12px 42px', borderRadius: '10px', border: '1px solid #1E293B', backgroundColor: '#0F172A', color: '#FFF', fontSize: '14px', outline: 'none' }}
                                    />
                                </div>
                            </div>

                            {!isForgotPassword && (
                                <div style={{ marginBottom: '12px' }}>
                                    <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: '#CBD5E1', marginBottom: '6px' }}>Password</label>
                                    <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                                        <Lock style={{ position: 'absolute', left: '14px', width: '16px', height: '16px', color: '#64748B' }} />
                                        <input
                                            type="password"
                                            required
                                            placeholder="••••••••"
                                            value={password}
                                            onChange={(e) => setPassword(e.target.value)}
                                            style={{ width: '100%', padding: '12px 14px 12px 42px', borderRadius: '10px', border: '1px solid #1E293B', backgroundColor: '#0F172A', color: '#FFF', fontSize: '14px', outline: 'none' }}
                                        />
                                    </div>
                                </div>
                            )}

                            {!isSignUp && !isForgotPassword && (
                                <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '20px' }}>
                                    <button
                                        type="button"
                                        onClick={() => setIsForgotPassword(true)}
                                        style={{ background: 'none', border: 'none', color: '#38BDF8', fontSize: '12px', cursor: 'pointer', padding: 0 }}
                                    >
                                        Forgot Password?
                                    </button>
                                </div>
                            )}
                        </>
                    )}

                    <button
                        type="submit"
                        disabled={loading}
                        style={{
                            width: '100%',
                            backgroundColor: '#3B82F6',
                            color: '#FFFFFF',
                            border: 'none',
                            padding: '12px',
                            borderRadius: '10px',
                            fontWeight: '600',
                            fontSize: '14px',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: '8px',
                            boxShadow: '0 4px 12px rgba(59, 130, 246, 0.4)'
                        }}
                    >
                        <Sparkles style={{ width: '16px', height: '16px' }} />
                        {loading ? 'Processing...' : (stepVerify ? 'Verify Code & Enter' : (isForgotPassword ? 'Send Reset Link' : (isSignUp ? 'Sign Up & Send Code' : 'Sign In')))}
                    </button>
                </form>

                {!stepVerify && (
                    <div style={{ marginTop: '20px', borderTop: '1px solid #1E293B', paddingTop: '16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                        <button
                            onClick={() => { setIsSignUp(!isSignUp); setIsForgotPassword(false); setMessage(null); setError(null); }}
                            style={{ background: 'none', border: 'none', color: '#CBD5E1', fontSize: '13px', cursor: 'pointer' }}
                        >
                            {isSignUp ? 'Already have an account? Sign In' : "Don't have an account? Sign Up"}
                        </button>

                        {isForgotPassword && (
                            <button
                                onClick={() => { setIsForgotPassword(false); setMessage(null); setError(null); }}
                                style={{ background: 'none', border: 'none', color: '#38BDF8', fontSize: '13px', cursor: 'pointer' }}
                            >
                                Back to Sign In
                            </button>
                        )}

                        <button
                            onClick={handleContinueAsGuest}
                            style={{
                                backgroundColor: 'transparent',
                                border: '1px solid rgba(255,255,255,0.2)',
                                color: '#FFFFFF',
                                padding: '10px',
                                borderRadius: '10px',
                                fontSize: '13px',
                                fontWeight: '500',
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: '6px',
                                marginTop: '6px'
                            }}
                        >
                            <span>Continue without signing in (Guest)</span>
                            <ArrowRight style={{ width: '14px', height: '14px' }} />
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}