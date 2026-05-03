import React, { useState, useEffect } from 'react';
import { Camera, Plus, Leaf, LogOut, ChevronRight, Loader2, Image as ImageIcon, ChevronLeft, Sparkles, ArrowLeft, CheckCircle2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { loginWithGoogle, uploadGardenPhotos, getUserGardens, getGardenDetails } from './services/api';
import Carousel from './components/Carousel';
import GoogleLoginButton from './components/GoogleLoginButton';

const App = () => {
  // Auth and Navigation State
  const [user, setUser] = useState(() => JSON.parse(localStorage.getItem('garden_user')));
  const [currentPage, setCurrentPage] = useState('login');
  const [loading, setLoading] = useState(false);

  // Data State
  const [gardens, setGardens] = useState([]);
  const [selectedGarden, setSelectedGarden] = useState(null);
  const [gardenDetails, setGardenDetails] = useState(null);

  // Form and Upload State
  const [newGardenName, setNewGardenName] = useState('');
  const [selectedPhotos, setSelectedPhotos] = useState([]);
  const [uploading, setUploading] = useState(false);

  // Initial Auth Sync and Navigation
  useEffect(() => {
    if (user) {
      fetchGardens();
      const interval = setInterval(fetchGardens, 5000); // Polling for AI status updates
      return () => clearInterval(interval);
    } else {
      setCurrentPage('login');
    }
  }, [user]);

  // Navigate to correct page based on garden count
  useEffect(() => {
    if (user && gardens.length > 0 && currentPage === 'login') {
      setCurrentPage('gardens');
    } else if (user && gardens.length === 0 && currentPage === 'login') {
      setCurrentPage('create_garden');
    }
  }, [gardens]);

  const fetchGardens = async () => {
    try {
      if (user?.user_id) {
        const data = await getUserGardens(user.user_id);
        setGardens(data);
      }
    } catch (err) {
      console.error("Failed to fetch gardens", err);
    }
  };

  const handleGoogleLogin = async () => {
    setLoading(true);
    try {
      const data = await loginWithGoogle(); // Mocked
      setUser(data);
      localStorage.setItem('garden_user', JSON.stringify(data));
    } catch (err) {
      alert("Login failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('garden_user');
    setGardens([]);
    setCurrentPage('login');
  };

  const handleOpenGarden = async (garden) => {
    setSelectedGarden(garden);
    setLoading(true);
    try {
      const details = await getGardenDetails(garden.id);
      setGardenDetails(details);
      setCurrentPage('plants');
    } catch (err) {
      alert("Failed to load garden details.");
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (selectedPhotos.length === 0) return;
    setUploading(true);
    try {
      await uploadGardenPhotos(selectedPhotos, newGardenName, user.user_id);
      setNewGardenName('');
      setSelectedPhotos([]);
      await fetchGardens();
      setCurrentPage('gardens');
    } catch (err) {
      alert("Upload failed.");
    } finally {
      setUploading(false);
    }
  };

  // --- Sub-Components (Pages) ---

  const LoginPage = () => (
    <div className="min-h-screen flex items-center justify-center p-6 bg-gradient-to-br from-slate-900 to-slate-800">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card p-12 w-full max-w-md text-center"
      >
        <div className="flex justify-center mb-8">
          <div className="bg-primary/20 p-5 rounded-full relative">
            <Leaf size={48} className="text-primary" />
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
              className="absolute -top-1 -right-1"
            >
              <Sparkles size={20} className="text-secondary" />
            </motion.div>
          </div>
        </div>
        <h1 className="text-5xl font-extrabold mb-4 tracking-tight">CareMyPlants</h1>
        <p className="text-text-muted mb-10 text-lg">AI-powered garden intelligence for your home.</p>
        <GoogleLoginButton onClick={handleGoogleLogin} loading={loading} />
      </motion.div>
    </div>
  );

  const [isProcessing, setIsProcessing] = useState(false);
  const [logs, setLogs] = useState([]);
  const [showLogs, setShowLogs] = useState(false);

  const handleStartProcessing = () => {
    setLogs([]);
    setShowLogs(true);
    setIsProcessing(true);
    
    // In a real app, API_BASE_URL would be used
    const eventSource = new EventSource('https://caremyplants-1059916488233.europe-west1.run.app/jobs/process?stream=true');
    
    eventSource.onmessage = (event) => {
      if (event.data === '[DONE]') {
        eventSource.close();
        setIsProcessing(false);
        fetchGardens();
        return;
      }
      setLogs(prev => [...prev.slice(-20), event.data]); // Keep last 20 logs
    };

    eventSource.onerror = (err) => {
      console.error("SSE Error:", err);
      eventSource.close();
      setIsProcessing(false);
      setLogs(prev => [...prev, "Connection lost or finished."]);
    };
  };

  const GardensPage = () => (
    <div className="min-h-screen p-6 md:p-12 max-w-7xl mx-auto">
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-16">
        <div>
          <h2 className="text-text-muted text-sm font-bold uppercase tracking-widest mb-1">Your Collection</h2>
          <h1 className="text-4xl font-extrabold gradient-text">My Oasis</h1>
        </div>
        <div className="flex flex-wrap items-center gap-4">
          {gardens.some(g => g.status === 'Ready to Process' || g.status === 'New') && (
            <button 
              onClick={handleStartProcessing} 
              disabled={isProcessing}
              className="btn-secondary flex items-center gap-2"
            >
              <Sparkles size={20} className={isProcessing ? "animate-spin" : ""} />
              {isProcessing ? 'Processing...' : 'Initialize AI Analysis'}
            </button>
          )}
          <button onClick={() => setCurrentPage('create_garden')} className="btn-primary flex items-center gap-2">
            <Plus size={20} />
            Add Garden
          </button>
          <button onClick={handleLogout} className="p-2 text-text-muted hover:text-white transition-colors">
            <LogOut size={24} />
          </button>
        </div>
      </header>

      <AnimatePresence>
        {showLogs && (
          <motion.div 
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-8 glass-card p-6 overflow-hidden"
          >
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-sm font-bold uppercase tracking-widest text-primary flex items-center gap-2">
                <Loader2 size={16} className="animate-spin" />
                Live AI Logs
              </h3>
              <button onClick={() => setShowLogs(false)} className="text-xs text-text-muted hover:text-white">Close</button>
            </div>
            <div className="bg-black/40 rounded-xl p-4 font-mono text-xs space-y-1 max-h-40 overflow-y-auto">
              {logs.length === 0 && <p className="text-text-muted">Connecting to AI core...</p>}
              {logs.map((log, i) => (
                <div key={i} className="text-emerald-400/80 border-l-2 border-emerald-500/30 pl-3 py-1">
                  {log}
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <Carousel>
        {gardens.map((garden) => (
          <div key={garden.id} className="glass-card glass-card-hover p-8 h-full flex flex-col justify-between">
            <div>
              <div className="flex justify-between items-start mb-6">
                <div className="bg-primary/10 p-4 rounded-2xl">
                  <Leaf className="text-primary" size={32} />
                </div>
                <span className={`status-badge ${garden.status === 'Ready' ? 'status-ready' : 'status-processing'}`}>
                  {garden.status}
                </span>
              </div>
              <h3 className="text-2xl font-bold mb-2">{garden.name}</h3>
              <p className="text-text-muted mb-8 italic">"{garden.status === 'Ready' ? 'Thriving and healthy.' : 'Analyzing plant health...'}"</p>
            </div>
            <button
              onClick={() => handleOpenGarden(garden)}
              disabled={garden.status !== 'Ready'}
              className="w-full py-4 rounded-2xl bg-white/10 hover:bg-white/20 text-white font-bold flex items-center justify-center gap-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              View Plants
              <ChevronRight size={20} />
            </button>
          </div>
        ))}
      </Carousel>
    </div>
  );

  const PlantsPage = () => (
    <div className="min-h-screen p-6 md:p-12 max-w-7xl mx-auto">
      <header className="mb-12">
        <button
          onClick={() => setCurrentPage('gardens')}
          className="flex items-center gap-2 text-text-muted hover:text-white transition-colors mb-6 font-semibold"
        >
          <ArrowLeft size={20} />
          Back to Gardens
        </button>
        <div className="flex justify-between items-end">
          <div>
            <h2 className="text-text-muted text-sm font-bold uppercase tracking-widest mb-1">{selectedGarden?.name}</h2>
            <h1 className="text-4xl font-extrabold gradient-text">Health Report</h1>
          </div>
          <div className="flex items-center gap-4">
            <div className="bg-primary/10 px-4 py-2 rounded-xl text-primary font-bold flex items-center gap-2">
              <Sparkles size={18} />
              AI Analysis Live
            </div>
            <button onClick={handleLogout} className="p-2 text-text-muted hover:text-white transition-colors">
              <LogOut size={24} />
            </button>
          </div>
        </div>
      </header>

      {loading ? (
        <div className="flex flex-col items-center justify-center py-20">
          <Loader2 className="animate-spin text-primary mb-4" size={48} />
          <p className="text-text-muted animate-pulse">Fetching plant intelligence...</p>
        </div>
      ) : (
        <Carousel>
          {gardenDetails?.plants.map((plant) => (
            <div key={plant.id} className="glass-card overflow-hidden h-full flex flex-col">
              <div className="relative h-64 overflow-hidden">
                <img
                  src={plant.image_url.startsWith('http') ? plant.image_url : `/static/${plant.image_url.split('/').pop()}`}
                  className="w-full h-full object-cover transition-transform duration-700 hover:scale-110"
                  alt={plant.name}
                />
                <div className="absolute top-4 right-4 capitalize bg-slate-900/80 backdrop-blur-md px-3 py-1 rounded-lg text-xs font-bold">
                  {plant.plant_variety || 'Unknown Species'}
                </div>
              </div>
              <div className="p-8 flex-grow">
                <h3 className="text-2xl font-bold mb-4">{plant.name}</h3>
                <div className="space-y-4">
                  <div className="bg-white/5 p-4 rounded-xl">
                    <p className="text-sm font-bold text-primary uppercase mb-1">Recommendation</p>
                    <p className="text-sm leading-relaxed">{plant.latest_recommendation || "Maintain current watering schedule."}</p>
                  </div>
                  <div className="bg-white/5 p-4 rounded-xl">
                    <p className="text-sm font-bold text-secondary uppercase mb-1">Current Condition</p>
                    <p className="text-sm italic text-text-muted">{plant.latest_condition || "Analyzing..."}</p>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </Carousel>
      )}
    </div>
  );

  const CreateGardenPage = () => (
    <div className="min-h-screen p-6 md:p-12 max-w-7xl mx-auto">
      <header className="mb-12">
        <div className="flex justify-between items-center mb-6">
          {gardens.length > 0 ? (
            <button
              onClick={() => setCurrentPage('gardens')}
              className="flex items-center gap-2 text-text-muted hover:text-white transition-colors font-semibold"
            >
              <ArrowLeft size={20} />
              Cancel
            </button>
          ) : <div></div>}
          <button onClick={handleLogout} className="p-2 text-text-muted hover:text-white transition-colors">
            <LogOut size={24} />
          </button>
        </div>
        <h1 className="text-5xl font-extrabold tracking-tight mb-4">Create your garden</h1>
        <p className="text-text-muted text-xl max-w-2xl">Capture your garden space from multiple angles to ensure every plant is identified and analyzed by our AI.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
        <div className="space-y-8">
          <div className="glass-card p-8">
            <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
              <Camera size={24} className="text-primary" />
              Upload Garden Photos
            </h3>
            <form onSubmit={handleUpload} className="space-y-6">
              <input
                type="text"
                value={newGardenName}
                onChange={(e) => setNewGardenName(e.target.value)}
                className="input-field"
                placeholder="Give your garden a name (e.g. Sunny Balcony)"
                required
              />
              <label className="border-2 border-dashed border-glass-border rounded-3xl p-12 flex flex-col items-center justify-center cursor-pointer hover:border-primary transition-all hover:bg-white/5">
                <ImageIcon size={48} className="text-text-muted mb-4" />
                <div className="text-center">
                  <p className="text-lg font-bold mb-1">
                    {selectedPhotos.length > 0 ? `${selectedPhotos.length} photos ready` : "Drop photos or click to browse"}
                  </p>
                  <p className="text-sm text-text-muted">High-res JPG or PNG works best</p>
                </div>
                <input type="file" multiple className="hidden" onChange={(e) => setSelectedPhotos(Array.from(e.target.files))} accept="image/*" />
              </label>
              <button
                disabled={uploading || selectedPhotos.length === 0}
                className="btn-primary w-full py-5 text-lg flex items-center justify-center gap-3"
              >
                {uploading ? <Loader2 className="animate-spin" size={24} /> : (
                  <>
                    <Sparkles size={24} />
                    Initialize AI Analysis
                  </>
                )}
              </button>
            </form>
          </div>

          <div className="bg-secondary/10 p-8 rounded-[32px] border border-secondary/20">
            <h4 className="font-bold text-secondary text-lg mb-4">Pro Tips for Best Results:</h4>
            <ul className="space-y-3 text-sm font-medium">
              <li className="flex items-start gap-2">
                <div className="mt-1 bg-secondary rounded-full p-1"><CheckCircle2 size={12} className="text-white" /></div>
                Use bright, natural daylight.
              </li>
              <li className="flex items-start gap-2">
                <div className="mt-1 bg-secondary rounded-full p-1"><CheckCircle2 size={12} className="text-white" /></div>
                Take overhead and side-profile shots.
              </li>
              <li className="flex items-start gap-2">
                <div className="mt-1 bg-secondary rounded-full p-1"><CheckCircle2 size={12} className="text-white" /></div>
                Ensure all leaves and stems are visible.
              </li>
            </ul>
          </div>
        </div>

        <div className="space-y-6">
          <h3 className="text-xl font-bold px-2 uppercase tracking-widest text-text-muted opacity-50">Inspiration</h3>
          <Carousel>
            {[1, 2, 3].map((i) => (
              <div key={i} className="glass-card overflow-hidden h-96">
                <img src={`/samples/garden_sample_${i}.png`} className="w-full h-full object-cover" alt="Garden Sample" />
              </div>
            ))}
          </Carousel>
        </div>
      </div>
    </div>
  );

  // --- Main Render Logic ---

  const renderPage = () => {
    switch (currentPage) {
      case 'login': return <LoginPage />;
      case 'gardens': return <GardensPage />;
      case 'plants': return <PlantsPage />;
      case 'create_garden': return <CreateGardenPage />;
      default: return <LoginPage />;
    }
  };

  return (
    <div className="min-h-screen">
      <AnimatePresence mode="wait">
        <motion.div
          key={currentPage}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ duration: 0.3 }}
        >
          {renderPage()}
        </motion.div>
      </AnimatePresence>
    </div>
  );
};

export default App;
