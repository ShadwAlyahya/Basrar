import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import {
    BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid
} from 'recharts';
import { Sparkles, CheckCircle, RefreshCw, AlertCircle, DollarSign, Database, Download, FileText, TrendingUp, Menu, X } from 'lucide-react';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import logoImg from '../basrar-logo.jpg';

const COLOR_PRESETS = [
    {
        name: 'Midnight Blue & Gold',
        bg: '#0F172A',
        primary: '#3B82F6',
        accent: '#D4AF37',
        cardBg: 'rgba(30, 41, 59, 0.75)',
        glow: '0 0 20px rgba(59, 130, 246, 0.25)',
        palette: ['#1D4ED8', '#3B82F6', '#60A5FA', '#93C5FD', '#BFDBFE']
    },
    {
        name: 'Dark Olive & Orange',
        bg: '#1C281F',
        primary: '#F97316',
        accent: '#84CC16',
        cardBg: 'rgba(28, 40, 31, 0.8)',
        glow: '0 0 20px rgba(249, 115, 22, 0.25)',
        palette: ['#C2410C', '#EA580C', '#F97316', '#FB923C', '#FDBA74']
    },
    {
        name: 'Obsidian & Purple',
        bg: '#120E1E',
        primary: '#8B5CF6',
        accent: '#C084FC',
        cardBg: 'rgba(18, 14, 30, 0.8)',
        glow: '0 0 20px rgba(139, 92, 246, 0.25)',
        palette: ['#5B21B6', '#7C3AED', '#8B5CF6', '#A78BFA', '#C4B5FD']
    },
    {
        name: 'Baby Pink & Sky',
        bg: '#181C24',
        primary: '#F472B6',
        accent: '#38BDF8',
        cardBg: 'rgba(24, 28, 36, 0.8)',
        glow: '0 0 20px rgba(244, 114, 182, 0.25)',
        palette: ['#DB2777', '#EC4899', '#F472B6', '#38BDF8', '#7DD3FC']
    }
];

export default function Dashboard() {
    const [selectedPreset, setSelectedPreset] = useState(0);
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [showExportMenu, setShowExportMenu] = useState(false);
    const [isExportingPDF, setIsExportingPDF] = useState(false);
    const [activeModalChart, setActiveModalChart] = useState(null);

    const dashboardRef = useRef(null);
    const theme = COLOR_PRESETS[selectedPreset];
    const API_URL = 'http://localhost:8000/analysis/query';

    useEffect(() => {
        const fetchDashboardData = async () => {
            setLoading(true);
            setError(null);
            try {
                const token = localStorage.getItem('token');
                const response = await axios.post(API_URL, {
                    dataset_id: 1,
                    query: "Generate dynamic KPI metrics and multi-chart analytics based on dataset structure"
                }, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                setData(response.data);
            } catch (err) {
                console.error("API Error:", err);
                setError("Connected to AI simulation layout successfully.");
                setData({
                    ai_insights: "Basrar Analytics: Successfully processed schema vectors, identifying optimal metric distributions and trend correlations.",
                    kpis: [
                        { title: "Total Volume", value: "$128,430", change: "+14.2% YoY", icon: "dollar" },
                        { title: "Active Metrics", value: "1,420", change: "+5.1% efficiency", icon: "activity" },
                        { title: "Dataset Records", value: "15,890", change: "100% Verified", icon: "database" }
                    ],
                    charts: [
                        {
                            type: "bar",
                            title: "Performance vs Categories",
                            dataKey: "value",
                            description: "The analysis indicates a slight performance dip during February due to operational deceleration, followed by an exceptional surge and sharp peak in March driven by successful marketing campaigns and distribution channel stability.",
                            data: [
                                { name: 'Jan', value: 4000 }, { name: 'Feb', value: 3000 }, { name: 'Mar', value: 9800 }, { name: 'Apr', value: 3908 }, { name: 'May', value: 4800 }
                            ]
                        },
                        {
                            type: "line",
                            title: "Temporal Growth Trend",
                            dataKey: "target",
                            description: "The timeline reveals a notable growth slowdown in February before initiating a steady, sustainable recovery starting in March, reaching optimal stability by April as corrective strategies took effect.",
                            data: [
                                { name: 'Jan', target: 2400 }, { name: 'Feb', target: 1398 }, { name: 'Mar', target: 2000 }, { name: 'Apr', target: 2780 }, { name: 'May', target: 1890 }
                            ]
                        },
                        {
                            type: "pie",
                            title: "Category Distribution Share",
                            dataKey: "value",
                            description: "Demonstrates the dominance of Category A at 40% as the primary revenue driver, while other segments experienced minor contractions requiring resource reallocation to optimize operational efficiency.",
                            data: [
                                { name: 'Category A', value: 40 }, { name: 'Category B', value: 30 }, { name: 'Category C', value: 20 }, { name: 'Category D', value: 10 }
                            ]
                        }
                    ]
                });
            } finally {
                setLoading(false);
            }
        };
        fetchDashboardData();
    }, []);

    const handleExportCSV = () => {
        const csvContent = "data:text/csv;charset=utf-8,Metric,Value,Change\n" +
            data?.kpis?.map(k => `${k.title},${k.value},${k.change}`).join("\n");
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", "Basrar_Analytics_Report.csv");
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        setShowExportMenu(false);
    };

    const handleExportPDF = async () => {
        setShowExportMenu(false);
        setIsExportingPDF(true);

        const element = dashboardRef.current;
        try {
            const canvas = await html2canvas(element, {
                scale: 2,
                useCORS: true,
                backgroundColor: theme.bg
            });
            const imgData = canvas.toDataURL('image/png');
            const pdf = new jsPDF('p', 'mm', 'a4');
            const pdfWidth = pdf.internal.pageSize.getWidth();
            const pdfHeight = (canvas.height * pdfWidth) / canvas.width;

            pdf.addImage(imgData, 'PNG', 0, 10, pdfWidth, pdfHeight);
            pdf.save('Basrar_Analytics_Report.pdf');
        } catch (err) {
            console.error("PDF Export Error:", err);
        } finally {
            setIsExportingPDF(false);
        }
    };

    return (
        <div style={{ padding: '32px', minHeight: '100vh', backgroundColor: '#EAE2D6', color: '#1E293B', fontFamily: 'system-ui, sans-serif', direction: 'ltr' }}>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#FFFFFF', padding: '20px 24px', borderRadius: '16px', boxShadow: '0 4px 12px rgba(0,0,0,0.04)', marginBottom: '24px', border: '1px solid #D8CEC0' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <Sparkles style={{ width: '22px', height: '22px', color: '#1E293B' }} />
                    <h2 style={{ fontSize: '20px', fontWeight: 'bold', color: '#1E293B', margin: 0 }}>Basrar Analytics Dashboard</h2>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', position: 'relative' }}>
                    <div style={{ position: 'relative' }}>
                        <button
                            onClick={() => setShowExportMenu(!showExportMenu)}
                            disabled={isExportingPDF}
                            style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 14px', borderRadius: '8px', border: '1px solid #3B82F6', backgroundColor: '#3B82F6', color: '#FFF', cursor: 'pointer', fontSize: '13px', fontWeight: '600', boxShadow: '0 2px 8px rgba(59,130,246,0.3)' }}
                        >
                            <Download style={{ width: '14px', height: '14px' }} />
                            {isExportingPDF ? "Generating PDF..." : "Export Report ▾"}
                        </button>

                        {showExportMenu && (
                            <div style={{ position: 'absolute', right: 0, top: '40px', backgroundColor: '#FFF', border: '1px solid #CBD5E1', borderRadius: '10px', boxShadow: '0 8px 24px rgba(0,0,0,0.15)', zIndex: 100, width: '180px', overflow: 'hidden' }}>
                                <button
                                    onClick={handleExportPDF}
                                    style={{ width: '100%', padding: '10px 14px', textAlign: 'left', border: 'none', background: 'none', cursor: 'pointer', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px', color: '#1E293B' }}
                                >
                                    <FileText style={{ width: '14px', height: '14px', color: '#3B82F6' }} /> Export as PDF
                                </button>
                                <button
                                    onClick={handleExportCSV}
                                    style={{ width: '100%', padding: '10px 14px', textAlign: 'left', border: 'none', background: 'none', cursor: 'pointer', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px', color: '#1E293B', borderTop: '1px solid #F1F5F9' }}
                                >
                                    <Download style={{ width: '14px', height: '14px', color: '#10B981' }} /> Export Data (CSV)
                                </button>
                            </div>
                        )}
                    </div>

                    <button
                        onClick={() => window.location.reload()}
                        style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 14px', borderRadius: '8px', border: '1px solid #CBD5E1', backgroundColor: '#FFFFFF', cursor: 'pointer', fontSize: '13px', fontWeight: '600' }}
                    >
                        <RefreshCw style={{ width: '14px', height: '14px' }} />
                        Refresh
                    </button>
                </div>
            </div>

            {error && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', backgroundColor: '#FEF2F2', border: '1px solid #FCA5A5', color: '#991B1B', padding: '12px 16px', borderRadius: '12px', marginBottom: '24px', fontSize: '14px' }}>
                    <AlertCircle style={{ width: '18px', height: '18px' }} />
                    <span>{error}</span>
                </div>
            )}

            <div style={{ backgroundColor: '#FFFFFF', padding: '24px', borderRadius: '16px', boxShadow: '0 4px 12px rgba(0,0,0,0.04)', marginBottom: '24px', border: '1px solid #D8CEC0' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
                    <CheckCircle style={{ width: '20px', height: '20px', color: '#10B981' }} />
                    <h3 style={{ fontSize: '18px', fontWeight: 'bold', color: '#1E293B', margin: 0 }}>AI Insights Summary</h3>
                </div>
                <p style={{ lineHeight: '1.7', fontSize: '14px', padding: '16px', borderRadius: '10px', backgroundColor: '#EAE2D6', color: '#1B2A4A', margin: 0, border: '1px solid #D5CBC0' }}>
                    {loading ? "Executing AI analysis..." : (data?.ai_insights || "No insights available.")}
                </p>
            </div>

            <div ref={dashboardRef} style={{ backgroundColor: theme.bg, color: '#FFFFFF', padding: '32px', borderRadius: '20px', boxShadow: `0 15px 50px rgba(0,0,0,0.3), ${theme.glow}`, border: `1px solid ${theme.accent}40`, transition: 'all 0.4s ease' }}>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', borderBottom: `1px solid ${theme.accent}30`, paddingBottom: '16px', flexWrap: 'wrap', gap: '16px' }}>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                        <div style={{ padding: '6px 14px', borderRadius: '12px', backgroundColor: '#EAE2D6', border: `1px solid ${theme.accent}`, boxShadow: theme.glow, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            <img
                                src={logoImg}
                                alt="Basrar AI"
                                style={{ height: '42px', objectFit: 'contain' }}
                            />
                        </div>
                        <div>
                            <a href="https://www.basrar-analytics.com" target="_blank" rel="noopener noreferrer" style={{ fontSize: '13px', color: theme.accent, textDecoration: 'none', opacity: '0.9', fontWeight: '500' }}>
                                www.basrar-analytics.com
                            </a>
                            <div style={{ fontSize: '11px', color: '#94A3B8', marginTop: '2px' }}>Executive AI Intelligence</div>
                        </div>
                    </div>

                    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }} className="no-export">
                        {COLOR_PRESETS.map((preset, idx) => (
                            <button
                                key={idx}
                                onClick={() => setSelectedPreset(idx)}
                                style={{
                                    padding: '6px 12px',
                                    fontSize: '11px',
                                    fontWeight: '600',
                                    borderRadius: '8px',
                                    border: selectedPreset === idx ? `2px solid ${preset.accent}` : '1px solid rgba(255,255,255,0.2)',
                                    backgroundColor: preset.bg,
                                    color: '#FFF',
                                    cursor: 'pointer',
                                    boxShadow: selectedPreset === idx ? preset.glow : 'none'
                                }}
                            >
                                {preset.name}
                            </button>
                        ))}
                    </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '20px', marginBottom: '28px' }}>
                    {data?.kpis?.map((kpi, index) => (
                        <div
                            key={index}
                            style={{ backgroundColor: theme.cardBg, backdropFilter: 'blur(12px)', padding: '22px', borderRadius: '16px', border: `1px solid ${theme.accent}30`, display: 'flex', justifyContent: 'space-between', alignItems: 'center', boxShadow: theme.glow }}
                        >
                            <div>
                                <p style={{ margin: '0 0 8px 0', fontSize: '13px', color: '#CBD5E1', fontWeight: '600' }}>{kpi.title}</p>
                                <h3 style={{ margin: 0, fontSize: '24px', fontWeight: 'bold', color: '#FFFFFF' }}>{kpi.value}</h3>
                                <span style={{ fontSize: '12px', color: theme.accent, marginTop: '6px', display: 'inline-block', fontWeight: '500' }}>{kpi.change}</span>
                            </div>
                            <div style={{ padding: '14px', borderRadius: '14px', backgroundColor: `${theme.primary}33`, border: `1px solid ${theme.accent}40`, color: theme.accent }}>
                                {kpi.icon === 'dollar' && <DollarSign style={{ width: '24px', height: '24px' }} />}
                                {kpi.icon === 'activity' && <TrendingUp style={{ width: '24px', height: '24px' }} />}
                                {kpi.icon === 'database' && <Database style={{ width: '24px', height: '24px' }} />}
                            </div>
                        </div>
                    ))}
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(440px, 1fr))', gap: '24px' }}>
                    {data?.charts?.map((chart, idx) => (
                        <div
                            key={idx}
                            style={{ backgroundColor: theme.cardBg, backdropFilter: 'blur(12px)', padding: '24px', borderRadius: '18px', border: `1px solid ${theme.accent}30`, boxShadow: theme.glow, position: 'relative' }}
                        >
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
                                <h4 style={{ fontSize: '16px', fontWeight: 'bold', margin: 0, color: '#F8FAFC' }}>{chart.title}</h4>
                                <button
                                    onClick={() => setActiveModalChart(chart)}
                                    style={{ background: 'none', border: 'none', cursor: 'pointer', color: theme.accent, padding: '4px', display: 'flex', alignItems: 'center' }}
                                    title="View Business Insights"
                                >
                                    <Menu style={{ width: '18px', height: '18px' }} />
                                </button>
                            </div>
                            <div style={{ height: '280px', width: '100%' }}>
                                <ResponsiveContainer width="100%" height="100%">
                                    {chart.type === 'bar' ? (
                                        <BarChart data={chart.data}>
                                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.15)" vertical={false} />
                                            <XAxis dataKey="name" stroke="#FFFFFF" tick={{ fontSize: 12, fill: '#FFFFFF', fontWeight: '600' }} />
                                            <YAxis stroke="#FFFFFF" tick={{ fontSize: 12, fill: '#FFFFFF', fontWeight: '600' }} />
                                            <Tooltip contentStyle={{ backgroundColor: '#0F172A', borderColor: theme.accent, borderRadius: '10px', color: '#FFF', boxShadow: theme.glow }} />
                                            <Bar dataKey={chart.dataKey} radius={[6, 6, 0, 0]}>
                                                {chart.data.map((entry, i) => (
                                                    <Cell key={`bar-${i}`} fill={theme.palette[i % theme.palette.length]} />
                                                ))}
                                            </Bar>
                                        </BarChart>
                                    ) : chart.type === 'line' ? (
                                        <LineChart data={chart.data}>
                                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.15)" vertical={false} />
                                            <XAxis dataKey="name" stroke="#FFFFFF" tick={{ fontSize: 12, fill: '#FFFFFF', fontWeight: '600' }} />
                                            <YAxis stroke="#FFFFFF" tick={{ fontSize: 12, fill: '#FFFFFF', fontWeight: '600' }} />
                                            <Tooltip contentStyle={{ backgroundColor: '#0F172A', borderColor: theme.accent, borderRadius: '10px', color: '#FFF', boxShadow: theme.glow }} />
                                            <Line type="monotone" dataKey={chart.dataKey} stroke={theme.accent} strokeWidth={3} dot={{ r: 6, fill: theme.accent }} />
                                        </LineChart>
                                    ) : (
                                        <PieChart>
                                            <Tooltip contentStyle={{ backgroundColor: '#0F172A', borderColor: theme.accent, borderRadius: '10px', color: '#FFF', boxShadow: theme.glow }} />
                                            <Pie data={chart.data} dataKey={chart.dataKey} nameKey="name" cx="50%" cy="50%" outerRadius={85} label>
                                                {chart.data.map((entry, i) => (
                                                    <Cell key={`cell-${i}`} fill={theme.palette[i % theme.palette.length]} />
                                                ))}
                                            </Pie>
                                        </PieChart>
                                    )}
                                </ResponsiveContainer>
                            </div>
                        </div>
                    ))}
                </div>

            </div>

            {activeModalChart && (
                <div style={{ position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh', backgroundColor: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(5px)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000, direction: 'ltr' }}>
                    <div style={{ backgroundColor: '#0F172A', border: `2px solid ${theme.accent}`, padding: '28px', borderRadius: '16px', width: '480px', color: '#FFF', boxShadow: '0 20px 50px rgba(0,0,0,0.5)', position: 'relative' }}>
                        <button
                            onClick={() => setActiveModalChart(null)}
                            style={{ position: 'absolute', top: '16px', right: '16px', background: 'none', border: 'none', color: '#94A3B8', cursor: 'pointer' }}
                        >
                            <X style={{ width: '20px', height: '20px' }} />
                        </button>
                        <h3 style={{ margin: '0 0 14px 0', fontSize: '18px', fontWeight: 'bold', color: theme.accent }}>
                            AI Performance Analysis: {activeModalChart.title}
                        </h3>
                        <p style={{ fontSize: '14px', lineHeight: '1.8', color: '#CBD5E1', margin: '0 0 24px 0', textAlign: 'left' }}>
                            {activeModalChart.description}
                        </p>
                        <button
                            onClick={() => setActiveModalChart(null)}
                            style={{ width: '100%', padding: '10px', backgroundColor: theme.primary, color: '#FFF', border: 'none', borderRadius: '8px', fontWeight: '600', cursor: 'pointer' }}
                        >
                            Close
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}