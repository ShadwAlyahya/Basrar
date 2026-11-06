import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Globe, LogIn, LogOut, History, Sparkles, X, FileText } from 'lucide-react';

export default function Header() {
    const navigate = useNavigate();

    const [isAuthenticated, setIsAuthenticated] = useState(
        localStorage.getItem('basrar_auth') === 'true'
    );
    const userName = localStorage.getItem('basrar_user_name') || 'Shadw';
    const lang = localStorage.getItem('basrar_lang') || 'EN';

    // حالة ظهور نافذة السجل (History Modal)
    const [isHistoryOpen, setIsHistoryOpen] = useState(false);
    const [historyItems, setHistoryItems] = useState([]);

    const handleLoginToggle = () => {
        if (isAuthenticated) {
            localStorage.removeItem('basrar_auth');
            setIsAuthenticated(false);
            navigate('/');
        } else {
            localStorage.setItem('basrar_auth', 'true');
            localStorage.setItem('basrar_user_name', 'Shadw');
            setIsAuthenticated(true);
            navigate('/upload');
        }
    };

    const handleLanguageToggle = () => {
        const newLang = lang === 'EN' ? 'AR' : 'EN';
        localStorage.setItem('basrar_lang', newLang);
        window.location.reload();
    };

    const openHistoryModal = () => {
        const savedHistory = JSON.parse(localStorage.getItem('basrar_history') || '[]');
        setHistoryItems(savedHistory);
        setIsHistoryOpen(true);
    };

    const t = {
        EN: {
            greetingUser: `Hello, ${userName}`,
            greetingGuest: "Hi, Guest Analyst!",
            tagline: "Smart Analytics Engine",
            history: "History",
            signOut: "Sign Out",
            signIn: "Sign In / Register",
            historyTitle: "Analysis History",
            noHistory: "No previous analyses found. Upload a dataset to begin!",
            close: "Close"
        },
        AR: {
            greetingUser: `أهلاً بك، ${userName}`,
            greetingGuest: "أهلاً بك يا ضيفنا الكريم!",
            tagline: "محرك التحليلات الذكية",
            history: "السجل",
            signOut: "تسجيل الخروج",
            signIn: "تسجيل الدخول / التسجيل",
            historyTitle: "سجل التحليلات السابقة",
            noHistory: "لا توجد تحليلات سابقة. قم برفع مجموعة بيانات للبدء!",
            close: "إغلاق"
        }
    };

    const currentText = t[lang];

    return (
        <>
            <header style={{
                width: '100%',
                padding: '16px 40px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                backgroundColor: '#EAE2D6',
                borderBottom: '2px solid #3A4D39',
                boxSizing: 'border-box',
                position: 'sticky',
                top: 0,
                zIndex: 1000,
                fontFamily: 'system-ui, sans-serif',
                direction: lang === 'AR' ? 'rtl' : 'ltr'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Sparkles style={{ width: '16px', height: '16px', color: '#3A4D39' }} />
                    <span style={{ fontSize: '14px', fontWeight: '700', color: '#0F172A' }}>
                        {isAuthenticated ? currentText.greetingUser : currentText.greetingGuest}
                    </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
                    <div
                        style={{ cursor: 'pointer', textAlign: lang === 'AR' ? 'left' : 'right' }}
                        onClick={() => navigate('/upload')}
                    >
                        <span style={{ fontSize: '16px', fontWeight: '800', color: '#0F172A', letterSpacing: '0.5px' }}>
                            BASRAR
                        </span>
                        <span style={{ fontSize: '11px', fontWeight: '600', color: '#3A4D39', display: 'block' }}>
                            {currentText.tagline}
                        </span>
                    </div>

                    <button
                        onClick={handleLanguageToggle}
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '6px',
                            padding: '7px 12px',
                            borderRadius: '8px',
                            border: 'none',
                            backgroundColor: '#3A4D39',
                            color: '#FFF',
                            fontSize: '12px',
                            fontWeight: '600',
                            cursor: 'pointer',
                            boxShadow: '0 2px 8px rgba(58,77,57,0.2)'
                        }}
                    >
                        <Globe style={{ width: '13px', height: '13px' }} /> {lang === 'EN' ? 'العربية (AR)' : 'English (EN)'}
                    </button>

                    {isAuthenticated ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <button
                                onClick={openHistoryModal}
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '5px',
                                    padding: '7px 12px',
                                    borderRadius: '8px',
                                    border: '1px solid #3A4D39',
                                    backgroundColor: 'transparent',
                                    color: '#3A4D39',
                                    fontSize: '12px',
                                    fontWeight: '600',
                                    cursor: 'pointer'
                                }}
                            >
                                <History style={{ width: '13px', height: '13px' }} /> {currentText.history}
                            </button>

                            <button
                                onClick={handleLoginToggle}
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '5px',
                                    padding: '7px 12px',
                                    borderRadius: '8px',
                                    border: 'none',
                                    backgroundColor: '#991B1B',
                                    color: '#FFF',
                                    fontSize: '12px',
                                    fontWeight: '600',
                                    cursor: 'pointer'
                                }}
                            >
                                <LogOut style={{ width: '13px', height: '13px' }} /> {currentText.signOut}
                            </button>
                        </div>
                    ) : (
                        <button
                            onClick={handleLoginToggle}
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '5px',
                                padding: '7px 12px',
                                borderRadius: '8px',
                                border: '1px solid #3A4D39',
                                backgroundColor: 'transparent',
                                color: '#3A4D39',
                                fontSize: '12px',
                                fontWeight: '600',
                                cursor: 'pointer'
                            }}
                        >
                            <LogIn style={{ width: '13px', height: '13px' }} /> {currentText.signIn}
                        </button>
                    )}
                </div>
            </header>

            {/* نافذة السجل المنبثقة (History Modal) */}
            {isHistoryOpen && (
                <div style={{
                    position: 'fixed',
                    top: 0,
                    left: 0,
                    width: '100vw',
                    height: '100vh',
                    backgroundColor: 'rgba(0, 0, 0, 0.6)',
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    zIndex: 2000,
                    direction: lang === 'AR' ? 'rtl' : 'ltr'
                }}>
                    <div style={{
                        backgroundColor: '#0F172A',
                        padding: '30px',
                        borderRadius: '20px',
                        width: '90%',
                        maxWidth: '550px',
                        maxHeight: '80vh',
                        overflowY: 'auto',
                        border: '1px solid #D4AF3740',
                        color: '#FFF',
                        boxShadow: '0 25px 50px rgba(0,0,0,0.5)'
                    }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', borderBottom: '1px solid #334155', paddingBottom: '12px' }}>
                            <h3 style={{ margin: 0, fontSize: '18px', fontWeight: '700', color: '#E2E8F0', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <History style={{ color: '#3B82F6', width: '20px', height: '20px' }} /> {currentText.historyTitle}
                            </h3>
                            <button
                                onClick={() => setIsHistoryOpen(false)}
                                style={{ background: 'transparent', border: 'none', color: '#94A3B8', cursor: 'pointer' }}
                            >
                                <X style={{ width: '20px', height: '20px' }} />
                            </button>
                        </div>

                        {historyItems.length === 0 ? (
                            <p style={{ textAlign: 'center', color: '#94A3B8', padding: '30px 0', fontSize: '14px' }}>
                                {currentText.noHistory}
                            </p>
                        ) : (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                                {historyItems.map((item) => (
                                    <div
                                        key={item.id}
                                        onClick={() => {
                                            setIsHistoryOpen(false);
                                            navigate('/dashboard');
                                        }}
                                        style={{
                                            backgroundColor: '#1E293B',
                                            padding: '16px',
                                            borderRadius: '12px',
                                            border: '1px solid #334155',
                                            cursor: 'pointer',
                                            transition: 'all 0.2s'
                                        }}
                                    >
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                                            <span style={{ fontSize: '14px', fontWeight: '700', color: '#E2E8F0', display: 'flex', alignItems: 'center', gap: '6px' }}>
                                                <FileText style={{ width: '15px', height: '15px', color: '#10B981' }} /> {item.title}
                                            </span>
                                            <span style={{ fontSize: '11px', color: '#94A3B8' }}>{item.date}</span>
                                        </div>
                                        <p style={{ fontSize: '12px', color: '#94A3B8', margin: 0 }}>
                                            <strong style={{ color: '#CBD5E1' }}>{lang === 'AR' ? 'الهدف:' : 'Goal:'}</strong> {item.goal}
                                        </p>
                                    </div>
                                ))}
                            </div>
                        )}

                        <div style={{ marginTop: '20px', textAlign: 'center' }}>
                            <button
                                onClick={() => setIsHistoryOpen(false)}
                                style={{
                                    padding: '10px 24px',
                                    borderRadius: '10px',
                                    border: 'none',
                                    backgroundColor: '#3B82F6',
                                    color: '#FFF',
                                    fontWeight: '600',
                                    cursor: 'pointer',
                                    fontSize: '13px'
                                }}
                            >
                                {currentText.close}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}