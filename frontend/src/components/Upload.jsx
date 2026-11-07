import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { UploadCloud, FileSpreadsheet, ArrowRight, CheckCircle2, Cpu } from 'lucide-react';
import Header from './Header';
import logoImg from '../basrar-logo.jpg';

export default function Upload() {
    const navigate = useNavigate();
    const [fileName, setFileName] = useState('');
    const [selectedFile, setSelectedFile] = useState(null);
    const [analysisGoal, setAnalysisGoal] = useState('');
    const [isUploading, setIsUploading] = useState(false);
    const [, setError] = useState(null);

    const lang = localStorage.getItem('basrar_lang') || 'EN';

    const handleFileChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            setSelectedFile(e.target.files[0]);
            setFileName(e.target.files[0].name);
        }
    };

    const handleProcessDataset = async (e) => {
        e.preventDefault();
        if (!selectedFile) return;

        setIsUploading(true);
        setError(null);

        try {
            const formData = new FormData();
            formData.append('file', selectedFile);

            const uploadRes = await axios.post('http://localhost:8000/agent/sessions', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            const sessionId = uploadRes.data.session_id;
            localStorage.setItem('basrar_session_id', sessionId);

            await axios.post(`http://localhost:8000/agent/sessions/${sessionId}/run`, {
                goal: analysisGoal
            });

            setIsUploading(false);
            navigate('/dashboard');
        } catch (err) {
            console.error("Agent Processing Error:", err);
            setIsUploading(false);
            setError("Error processing dataset with AI agent.");
            alert(lang === 'AR' ? "حدث خطأ أثناء معالجة الملف عبر الذكاء الاصطناعي." : "Error processing dataset with AI agent.");
        }
    };

    return (
        <div style={{ minHeight: '100vh', backgroundColor: '#EAE2D6', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'flex-start', fontFamily: 'system-ui, sans-serif', boxSizing: 'border-box', direction: lang === 'AR' ? 'rtl' : 'ltr' }}>

            <Header />

            <div style={{ width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '50px 20px 150px 20px', boxSizing: 'border-box' }}>
                <div style={{ textAlign: 'center', marginBottom: '30px', width: '100%', maxWidth: '950px' }}>
                    <img
                        src={logoImg}
                        alt="Basrar AI"
                        style={{
                            width: '100%',
                            maxHeight: '210px',
                            objectFit: 'contain',
                            display: 'block',
                            margin: '0 auto'
                        }}
                    />
                    <p style={{ fontSize: '15px', color: '#0F172A', fontWeight: '600', margin: '16px 0 0 0', lineHeight: '1.5' }}>
                        {lang === 'AR'
                            ? "قم برفع مجموعة البيانات الخاصه بك ودع الذكاء الاصطناعي المتقدم لدينا يحلل بياناتك بالكامل ويصمم لوحات معلومات تنفيذية."
                            : "Upload your dataset and let our advanced AI analyze your data completely and engineer executive dashboards."}
                    </p>
                </div>

                <div style={{ backgroundColor: '#0F172A', padding: '36px', borderRadius: '24px', width: '100%', maxWidth: '540px', border: '1px solid #D4AF3740', boxShadow: '0 20px 50px rgba(0,0,0,0.25)', color: '#FFF', boxSizing: 'border-box' }}>

                    <form onSubmit={handleProcessDataset}>
                        <div style={{ border: '2px dashed #3B82F6', borderRadius: '16px', padding: '30px 20px', textAlign: 'center', backgroundColor: 'rgba(30, 41, 59, 0.5)', marginBottom: '20px', cursor: 'pointer', position: 'relative' }}>
                            <input
                                type="file"
                                accept=".csv, .xlsx, .xls"
                                onChange={handleFileChange}
                                required
                                style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', opacity: 0, cursor: 'pointer' }}
                            />
                            <UploadCloud style={{ width: '42px', height: '42px', color: '#3B82F6', marginBottom: '10px' }} />
                            <h4 style={{ margin: '0 0 6px 0', fontSize: '15px', color: '#E2E8F0' }}>
                                {fileName ? fileName : (lang === 'AR' ? "انقر أو اسحب وأفلت ملف البيانات هنا" : "Click or drag & drop data file here")}
                            </h4>
                            <p style={{ margin: 0, fontSize: '12px', color: '#64748B' }}>
                                {lang === 'AR' ? "يدعم ملفات CSV و XLSX حتى 50 ميجابايت" : "Supports CSV, XLSX up to 50MB"}
                            </p>
                        </div>

                        {fileName && (
                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', backgroundColor: '#1E293B', padding: '10px 14px', borderRadius: '10px', marginBottom: '20px', border: '1px solid #334155' }}>
                                <FileSpreadsheet style={{ width: '18px', height: '18px', color: '#10B981' }} />
                                <span style={{ fontSize: '13px', color: '#E2E8F0', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{fileName}</span>
                                <CheckCircle2 style={{ width: '16px', height: '16px', color: '#10B981' }} />
                            </div>
                        )}

                        <div style={{ marginBottom: '24px' }}>
                            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', color: '#CBD5E1', marginBottom: '8px', fontWeight: '600' }}>
                                <Cpu style={{ width: '15px', height: '15px', color: '#3B82F6' }} />
                                {lang === 'AR' ? "هدف التحليل / الهدف التجاري" : "Analysis Objective / Business Goal"}
                            </label>
                            <input
                                type="text"
                                required
                                value={analysisGoal}
                                onChange={(e) => setAnalysisGoal(e.target.value)}
                                placeholder={lang === 'AR' ? "مثل: تحليل اتجاهات الإيرادات الفصلية وخدمة العملاء..." : "e.g., Analyze quarterly revenue trends and customer sentiment..."}
                                style={{ width: '100%', padding: '12px 14px', borderRadius: '10px', border: '1px solid #334155', backgroundColor: '#1E293B', color: '#FFF', fontSize: '13px', outline: 'none', boxSizing: 'border-box' }}
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={!fileName || isUploading}
                            style={{
                                width: '100%',
                                padding: '13px',
                                borderRadius: '10px',
                                border: 'none',
                                backgroundColor: fileName ? '#3B82F6' : '#334155',
                                color: '#FFF',
                                fontWeight: 'bold',
                                fontSize: '14px',
                                cursor: fileName ? 'pointer' : 'not-allowed',
                                boxShadow: fileName ? '0 4px 16px rgba(59,130,246,0.35)' : 'none',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: '8px',
                                transition: 'all 0.3s'
                            }}
                        >
                            {isUploading
                                ? (lang === 'AR' ? "جاري تحليل البيانات وبناء لوحة المعلومات..." : "Analyzing Dataset & Building Dashboard...")
                                : (lang === 'AR' ? "إجراء تحليل الذكاء الاصطناعي وإنشاء لوحة المعلومات" : "Run AI Analysis & Generate Dashboard")}
                            <ArrowRight style={{ width: '16px', height: '16px', transform: lang === 'AR' ? 'scaleX(-1)' : 'none' }} />
                        </button>
                    </form>
                </div>

                <div style={{ textAlign: 'center', marginTop: '180px', maxWidth: '540px' }}>
                    <h3 style={{ fontSize: '20px', fontWeight: '800', color: '#000000', margin: '0 0 10px 0' }}>
                        {lang === 'AR' ? "من نحن" : "Who We Are"}
                    </h3>
                    <p style={{ fontSize: '14px', color: '#111827', lineHeight: '1.7', margin: 0, fontWeight: '500' }}>
                        {lang === 'AR'
                            ? "بصرار هي منصة ذكاء اصطناعي تنفيذية. نقوم باستيعاب مجموعات البيانات الخاصة بشركتك، وإجراء تحليلات شاملة للبيانات بناءً على أهدافك التحليلية الدقيقة، وتلقائياً ننشئ لوحات معلومات استخباراتية ديناميكية جاهزة للنشر وتوصيات استراتيجية."
                            : "Basrar is an executive AI intelligence platform. We ingest your raw business datasets, execute comprehensive data analysis based on your precise analytical objectives, and automatically generate dynamic, publication-ready intelligence dashboards and strategic recommendations."}
                    </p>
                </div>
            </div>

        </div>
    );
}