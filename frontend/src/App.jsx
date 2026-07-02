import React, { useState, useEffect } from 'react';
import { Camera, Plus, Leaf, LogOut, ChevronRight, Loader2, Image as ImageIcon, ChevronLeft, Sparkles, ArrowLeft, CheckCircle2, Droplets, Sun, Sprout, TrendingUp, Box, Scissors, Check, AlertCircle, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { loginWithGoogle, uploadGardenPhotos, getUserGardens, getGardenDetails, getWorkflowStatus, generateGardenVisualization } from './services/api';
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

  // Workflow and Status State
  const [activeUpdateId, setActiveUpdateId] = useState(null);
  const [workflowStatus, setWorkflowStatus] = useState(null);
  const [activeMetric, setActiveMetric] = useState(null);
  const [visualizing, setVisualizing] = useState(false);

  const activityFriendlyNames = {
    'GATHER_GARDEN_DETAILS': 'Analyzing garden overview...',
    'CUT_PLANT_IMAGES': 'Identifying individual plants...',
    'GATHER_PLANT_DETAILS': 'Analyzing each plant...',
    'UPDATE_GARDEN_FLAGS': 'Finalizing analysis...',
  };

  // Initial Auth Sync and Navigation
  useEffect(() => {
    if (user) {
      fetchGardens();
    } else {
      setCurrentPage('login');
    }
  }, [user]);

  // Polling for workflow status
  useEffect(() => {
    if (activeUpdateId) {
      const interval = setInterval(async () => {
        try {
          const statusData = await getWorkflowStatus(activeUpdateId);
          setWorkflowStatus(statusData);

          if (['COMPLETED', 'FAILED', 'TIMED_OUT', 'CANCELED'].includes(statusData.status)) {
            clearInterval(interval);
            setActiveUpdateId(null);
            setWorkflowStatus(null);
            await fetchGardens(); // Refresh garden list
          }
        } catch (error) {
          console.error("Failed to fetch workflow status", error);
          clearInterval(interval); // Stop polling on error
          setActiveUpdateId(null);
          setWorkflowStatus(null);
        }
      }, 3000);

      return () => clearInterval(interval);
    }
  }, [activeUpdateId]);


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
      const response = await uploadGardenPhotos(selectedPhotos, newGardenName, user.user_id);
      setNewGardenName('');
      setSelectedPhotos([]);
      setActiveUpdateId(response.garden_update_id);
      await fetchGardens(); // Fetch gardens immediately to show the new "Processing" garden
      setCurrentPage('gardens');
    } catch (err) {
      alert("Upload failed.");
    } finally {
      setUploading(false);
    }
  };

  const handleVisualize = async () => {
    if (!selectedGarden) return;
    setVisualizing(true);
    try {
      await generateGardenVisualization(selectedGarden.id);
      // Poll for updated garden details
      const interval = setInterval(async () => {
        try {
          const details = await getGardenDetails(selectedGarden.id);
          if (details.visualization) {
            setGardenDetails(details);
            setVisualizing(false);
            clearInterval(interval);
          }
        } catch (err) {
          console.error("Failed to poll for visualization", err);
          setVisualizing(false);
          clearInterval(interval);
        }
      }, 5000);
    } catch (err) {
      alert("Failed to start visualization.");
      setVisualizing(false);
    }
  };

  // --- Sub-Components (Pages) ---

  const LoginPage = () => (
    <div className="min-h-screen flex items-center justify-center p-6">
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

  const GardensPage = () => {
    const getGardenStatusInfo = (garden) => {
      if (workflowStatus && garden.latest_update_id === activeUpdateId) {
        let currentActivity = workflowStatus.activities?.find(a => a.status === 'RUNNING');
        if (!currentActivity) {
            currentActivity = workflowStatus.activities?.find(a => a.status === 'PENDING');
        }

        const statusText = currentActivity ? activityFriendlyNames[currentActivity.name] : 'Processing...';

        return {
          status: workflowStatus.status === 'RUNNING' ? 'Processing' : garden.status,
          message: statusText,
          isProcessing: true,
        };
      }
      return {
        status: garden.status,
        message: garden.status === 'Ready' ? 'Thriving and healthy.' : 'Analyzing plant health...',
        isProcessing: garden.status !== 'Ready',
      };
    };

    return (
      <div className="min-h-screen p-6 md:p-12 max-w-7xl mx-auto">
        <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-16">
          <div>
            <h2 className="text-text-muted text-sm font-bold uppercase tracking-widest mb-1">Your Collection</h2>
            <h1 className="text-4xl font-extrabold gradient-text">My Gardens</h1>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            <button onClick={() => setCurrentPage('create_garden')} className="btn-primary flex items-center gap-2">
              <Plus size={20} />
              Add Garden
            </button>
            <button onClick={handleLogout} className="p-2 text-text-muted hover:text-white transition-colors">
              <LogOut size={24} />
            </button>
          </div>
        </header>

        <Carousel>
          {gardens.map((garden) => {
            const { status, message, isProcessing } = getGardenStatusInfo(garden);
            return (
              <div key={garden.id} className="glass-card glass-card-hover p-8 h-full flex flex-col justify-between">
                <div>
                  <div className="flex justify-between items-start mb-6">
                    <div className="bg-primary/10 p-4 rounded-2xl">
                      <Leaf className="text-primary" size={32} />
                    </div>
                    <span className={`status-badge ${status === 'Ready' ? 'status-ready' : 'status-processing'}`}>
                      {isProcessing ? (
                        <Loader2 size={16} className="animate-spin mr-2" />
                      ) : null}
                      {status}
                    </span>
                  </div>
                  <h3 className="text-2xl font-bold mb-2">{garden.name}</h3>
                  <p className="text-text-muted mb-8 italic">"{message}"</p>
                </div>
                <button
                  onClick={() => handleOpenGarden(garden)}
                  disabled={status !== 'Ready'}
                  className="w-full py-4 rounded-2xl bg-primary/10 hover:bg-primary/20 text-primary font-bold flex items-center justify-center gap-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  View Plants
                  <ChevronRight size={20} />
                </button>
              </div>
            );
          })}
        </Carousel>
      </div>
    );
  };

  const PlantsPage = () => {
    const vitality = gardenDetails?.healthOverview?.sanctuaryVitality || {
      score: 85,
      flourishingPlantsCount: 12,
      careNeededPlantsCount: 4,
    };

    const metrics = gardenDetails?.healthOverview?.metrics || [
      { category: 'WATERING', status: 'High', isUnfavorable: true, affectedPlantsCount: 5, affectedPlantIds: [] },
      { category: 'SUN_EXPOSURE', status: 'Optimal', isUnfavorable: false, affectedPlantsCount: 0, affectedPlantIds: [] },
      { category: 'SOIL_QUALITY', status: 'Poor', isUnfavorable: true, affectedPlantsCount: 3, affectedPlantIds: [] },
      { category: 'VITALITY', status: 'Optimal', isUnfavorable: false, affectedPlantsCount: 0, affectedPlantIds: [] },
      { category: 'LEAF_CARE', status: 'Dusty', isUnfavorable: true, affectedPlantsCount: 4, affectedPlantIds: [] },
      { category: 'POT_STATUS', status: 'Balanced', isUnfavorable: false, affectedPlantsCount: 0, affectedPlantIds: [] },
      { category: 'PRUNING', status: 'Overdue', isUnfavorable: true, affectedPlantsCount: 4, affectedPlantIds: [] },
    ];

    const categoryIcons = {
      WATERING: Droplets,
      SUN_EXPOSURE: Sun,
      SOIL_QUALITY: Sprout,
      VITALITY: TrendingUp,
      LEAF_CARE: Sparkles,
      POT_STATUS: Box,
      PRUNING: Scissors
    };

    const categoryNames = {
      WATERING: 'Watering',
      SUN_EXPOSURE: 'Sun Exposure',
      SOIL_QUALITY: 'Soil Quality',
      VITALITY: 'Vitality',
      LEAF_CARE: 'Leaf Care',
      POT_STATUS: 'Pot Status',
      PRUNING: 'Pruning'
    };

    const radius = 24;
    const circumference = 2 * Math.PI * radius;
    const strokeDashoffset = circumference - (vitality.score / 100) * circumference;
    const isHealthyScore = vitality.score > 90;
    const radialColor = isHealthyScore ? '#aacec3' : '#D10056';

    return (
      <div className="min-h-screen bg-[#F7FAF9] p-6 md:p-12 max-w-7xl mx-auto flex flex-col">
        <header className="mb-8">
          <button
            onClick={() => setCurrentPage('gardens')}
            className="flex items-center gap-2 text-gray-500 hover:text-[#1A3C34] transition-colors mb-6 font-semibold"
          >
            <ArrowLeft size={20} />
            Back to Gardens
          </button>
          <div className="flex justify-between items-end">
            <div>
              <h2 className="text-[#1A3C34] opacity-60 text-sm font-bold uppercase tracking-widest mb-1">{selectedGarden?.name}</h2>
              <h1 className="text-4xl font-extrabold text-[#1A3C34]">Balanced Health Overview</h1>
            </div>
            <div className="flex items-center gap-4">
              <div className="bg-[#1A3C34]/10 px-4 py-2 rounded-xl text-[#1A3C34] font-bold flex items-center gap-2">
                <Sparkles size={18} />
                AI Analysis Live
              </div>
              <button onClick={handleLogout} className="p-2 text-gray-500 hover:text-[#1A3C34] transition-colors">
                <LogOut size={24} />
              </button>
            </div>
          </div>
        </header>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 flex-grow">
            <Loader2 className="animate-spin text-[#1A3C34] mb-4" size={48} />
            <p className="text-gray-500 animate-pulse font-medium">Fetching plant intelligence...</p>
          </div>
        ) : (
          <div className="space-y-8 flex-grow pb-12">
            {/* Sanctuary Vitality Section */}
            <div className="bg-[#1A3C34] text-white p-6 rounded-2xl flex items-center justify-between shadow-xl">
              <div className="flex flex-col">
                <span className="text-xs font-bold uppercase tracking-wider text-[#aacec3] opacity-80">SANCTUARY VITALITY</span>
                <h2 className="text-5xl font-extrabold my-2">{vitality.score}%</h2>
                <p className="text-sm text-[#eaf6f2] opacity-90">
                  {vitality.flourishingPlantsCount} plants are flourishing, {vitality.careNeededPlantsCount} need care
                </p>
              </div>
              <div className="relative w-16 h-16 flex items-center justify-center shrink-0">
                <svg className="w-full h-full transform -rotate-90">
                  <circle
                    cx="32"
                    cy="32"
                    r={radius}
                    stroke="#132c26"
                    strokeWidth="4"
                    fill="transparent"
                  />
                  <circle
                    cx="32"
                    cy="32"
                    r={radius}
                    stroke={radialColor}
                    strokeWidth="4"
                    fill="transparent"
                    strokeDasharray={circumference}
                    strokeDashoffset={strokeDashoffset}
                    strokeLinecap="round"
                    className="transition-all duration-500"
                  />
                </svg>
                <div className="absolute flex items-center justify-center">
                  <Leaf size={18} className="text-white fill-current" />
                </div>
              </div>
            </div>

            {/* Metric Tile Grid */}
            <div className="grid grid-cols-3 gap-3">
              {metrics.map((metric) => {
                const IconComponent = categoryIcons[metric.category] || Sprout;
                const displayName = categoryNames[metric.category] || metric.category;
                
                return (
                  <div
                    key={metric.category}
                    onClick={() => {
                      setActiveMetric(metric);
                    }}
                    className="bg-white border border-[#eaf6f2] hover:border-[#1A3C34] transition-all p-3 rounded-2xl relative flex flex-col items-center justify-center cursor-pointer shadow-sm min-h-[96px] text-center"
                  >
                    {metric.isUnfavorable && (
                      <div className="absolute top-2 right-2 bg-[#D10056] text-white text-[10px] font-bold w-5 h-5 rounded-full flex items-center justify-center shadow-md">
                        {metric.affectedPlantsCount}
                      </div>
                    )}
                    
                    <div className="mb-2">
                      <IconComponent
                        size={20}
                        className={metric.isUnfavorable ? "text-[#D10056]" : "text-[#1A3C34]"}
                      />
                    </div>
                    
                    <span className="text-[9px] text-gray-400 uppercase font-bold tracking-wider mb-1">
                      {displayName}
                    </span>
                    
                    <div className="flex items-center gap-1 justify-center">
                      <span className={`text-xs font-extrabold ${metric.isUnfavorable ? 'text-[#D10056]' : 'text-[#1A3C34]'}`}>
                        {metric.status}
                      </span>
                      {!metric.isUnfavorable && (
                        <Check size={12} className="text-emerald-600 stroke-[3]" />
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Garden Visualization Section */}
            <div className="bg-white p-6 rounded-2xl border border-[#eaf6f2] shadow-sm">
              <h2 className="text-2xl font-extrabold text-[#1A3C34] mb-4">Garden Visualization</h2>
              {visualizing ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <Loader2 className="animate-spin text-[#1A3C34] mb-4" size={32} />
                  <p className="text-gray-500 font-medium">Generating your garden's potential...</p>
                </div>
              ) : gardenDetails?.visualization ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <img src={gardenDetails.visualization.image_url} alt="Garden Visualization" className="rounded-xl object-cover w-full h-full" />
                  </div>
                  <div>
                    <h3 className="font-bold text-lg mb-2">Recommendations</h3>
                    <ul className="space-y-3">
                      {gardenDetails.visualization.recommendations.map((rec, index) => (
                        <li key={index} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                          <img src={rec.image_url} alt={rec.title} className="w-12 h-12 rounded-md object-cover" />
                          <div>
                            <a href={rec.product_url} target="_blank" rel="noopener noreferrer" className="font-bold text-sm hover:underline">{rec.title}</a>
                            <p className="text-xs text-gray-500">{rec.reason}</p>
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-gray-500 mb-4">See how your garden could look with a little love.</p>
                  <button onClick={handleVisualize} className="btn-primary flex items-center gap-2 mx-auto">
                    <Sparkles size={20} />
                    Visualize My Garden
                  </button>
                </div>
              )}
            </div>

            {/* My Plants Carousel Section */}
            <div>
              <h2 className="text-2xl font-extrabold text-[#1A3C34] mb-4">My Plants</h2>
              <Carousel>
                {gardenDetails?.plants.map((plant) => (
                  <div key={plant.id} className="bg-white rounded-3xl border border-[#eaf6f2] overflow-hidden shadow-sm h-full flex flex-col">
                    <div className="relative h-48 overflow-hidden">
                      <img
                        src={plant.image_url.startsWith('http') ? plant.image_url : `/static/${plant.image_url.split('/').pop()}`}
                        className="w-full h-full object-cover transition-transform duration-700 hover:scale-105"
                        alt={plant.name}
                      />
                      <div className="absolute top-4 right-4 capitalize bg-white/90 backdrop-blur-md px-3 py-1 rounded-xl text-xs font-bold text-[#1A3C34] border border-[#eaf6f2]">
                        {plant.plant_variety || 'Unknown Species'}
                      </div>
                    </div>
                    <div className="p-6 flex-grow flex flex-col justify-between">
                      <div>
                        <h3 className="text-xl font-bold text-[#1A3C34] mb-4">{plant.name}</h3>
                        <div className="space-y-3">
                          <div className="bg-[#f7faf9] p-3 rounded-xl border border-[#eaf6f2]">
                            <p className="text-xs font-extrabold text-[#1A3C34] uppercase mb-1">Recommendation</p>
                            <p className="text-xs leading-relaxed text-gray-600">{plant.latest_recommendation || "Maintain current watering schedule."}</p>
                          </div>
                          <div className="bg-[#f7faf9] p-3 rounded-xl border border-[#eaf6f2]">
                            <p className="text-xs font-extrabold text-[#D10056] uppercase mb-1">Current Condition</p>
                            <p className="text-xs italic text-gray-500">{plant.latest_condition || "Analyzing..."}</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </Carousel>
            </div>
          </div>
        )}

        {/* Bottom Sheet / Expanded View Modal */}
        <AnimatePresence>
          {activeMetric && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-[#01261f]/40 backdrop-blur-sm z-[100] flex items-end justify-center"
              onClick={() => setActiveMetric(null)}
            >
              <motion.div
                initial={{ y: "100%" }}
                animate={{ y: 0 }}
                exit={{ y: "100%" }}
                transition={{ type: "spring", damping: 25, stiffness: 350 }}
                className="bg-white w-full max-w-lg rounded-t-3xl shadow-2xl overflow-hidden p-6 max-h-[85vh] flex flex-col"
                onClick={(e) => e.stopPropagation()}
              >
                <div className="flex justify-between items-center border-b border-[#eaf6f2] pb-4 mb-4">
                  <div>
                    <span className="text-xs font-bold text-gray-400 uppercase tracking-widest">
                      {categoryNames[activeMetric.category] || activeMetric.category} Details
                    </span>
                    <h3 className="text-2xl font-extrabold text-[#1A3C34] flex items-center gap-2">
                      Status: <span className={activeMetric.isUnfavorable ? "text-[#D10056]" : "text-emerald-600"}>
                        {activeMetric.isUnfavorable ? activeMetric.status : "Optimal"}
                      </span>
                    </h3>
                  </div>
                  <button
                    onClick={() => setActiveMetric(null)}
                    className="p-2 bg-gray-100 hover:bg-gray-200 transition-colors rounded-full text-gray-500"
                  >
                    <X size={20} />
                  </button>
                </div>

                <div className="overflow-y-auto flex-grow space-y-4 pr-1">
                  {activeMetric.isUnfavorable ? (
                    gardenDetails?.plants.filter(p => activeMetric.affectedPlantIds.includes(p.id)).length > 0 ? (
                      gardenDetails?.plants.filter(p => activeMetric.affectedPlantIds.includes(p.id)).map((plant) => (
                        <div key={plant.id} className="flex gap-4 p-4 bg-[#f7faf9] rounded-2xl border border-[#eaf6f2]">
                          <div className="w-16 h-16 rounded-xl overflow-hidden shrink-0">
                            <img
                              src={plant.image_url.startsWith('http') ? plant.image_url : `/static/${plant.image_url.split('/').pop()}`}
                              className="w-full h-full object-cover"
                              alt={plant.name}
                            />
                          </div>
                          <div className="flex-grow flex flex-col justify-between">
                            <div>
                              <h4 className="font-bold text-[#1A3C34]">{plant.name}</h4>
                              <span className="text-xs text-gray-400 capitalize">{plant.plant_variety || 'Unknown Species'}</span>
                            </div>
                            
                            <div className="mt-2 text-xs font-bold text-[#D10056] bg-[#D10056]/5 py-1 px-3 rounded-lg border border-[#D10056]/20 inline-block w-fit">
                              {activeMetric.category === 'WATERING' && `Needs watering attention: ${plant.latest_condition || 'Dry/Overwatered'}`}
                              {activeMetric.category === 'SUN_EXPOSURE' && `Inadequate lighting: ${plant.latest_condition || 'Poor exposure'}`}
                              {activeMetric.category === 'SOIL_QUALITY' && `Needs fertilization: ${plant.latest_condition || 'Nutrient deficit'}`}
                              {activeMetric.category === 'VITALITY' && `Stagnant growth: ${plant.latest_condition || 'Low momentum'}`}
                              {activeMetric.category === 'LEAF_CARE' && `Leaf Care Overdue: ${plant.latest_condition || 'Dusty leaves'}`}
                              {activeMetric.category === 'POT_STATUS' && `Cramped Pot: ${plant.latest_condition || 'Needs repotting'}`}
                              {activeMetric.category === 'PRUNING' && `Overdue Trimming: ${plant.latest_condition || 'Overgrown/Dead leaves'}`}
                            </div>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="text-center py-8 text-gray-400 font-medium">
                        No specific plant records found for this issue, but general status needs attention.
                      </div>
                    )
                  ) : (
                    <div className="text-center py-12 flex flex-col items-center justify-center">
                      <div className="w-16 h-16 bg-emerald-50 rounded-full flex items-center justify-center text-emerald-600 mb-4">
                        <Check size={36} className="stroke-[3]" />
                      </div>
                      <h4 className="font-bold text-[#1A3C34] text-lg mb-1">All Good!</h4>
                      <p className="text-sm text-gray-400 max-w-xs">
                        All plants in this sanctuary are currently healthy and have optimal {categoryNames[activeMetric.category]?.toLowerCase() || 'conditions'}.
                      </p>
                    </div>
                  )}
                </div>

                <div className="pt-4 mt-4 border-t border-[#eaf6f2]">
                  <button
                    onClick={() => setActiveMetric(null)}
                    className="w-full py-4 bg-[#1A3C34] hover:bg-[#132c26] text-white font-bold rounded-2xl transition-all shadow-md"
                  >
                    Done
                  </button>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    );
  };

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
                className="input-.field"
                placeholder="Give your garden a name (e.g. Sunny Balcony)"
                required
              />
              <label className="border-2 border-dashed border-glass-border rounded-3xl p-12 flex flex-col items-center justify-center cursor-pointer hover:border-primary transition-all hover:bg-primary/5">
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
                    Upload and Analyze
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
