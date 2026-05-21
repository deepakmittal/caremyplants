import React, { useEffect, useState } from 'react';
import { getDetailedGardens, uploadGardenPhotos } from './services/api';
import { motion, AnimatePresence } from 'framer-motion';
import { Leaf, ChevronRight, Loader2, ArrowLeft, Thermometer, Droplets, Sun, Plus, Image as ImageIcon, Sparkles } from 'lucide-react';
import './index.css';

const SanctuaryCard = ({ garden, index, onClick }) => {
  const photoUrl = garden.photos && garden.photos.length > 0
    ? garden.photos[0].photo_url
    : 'https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?auto=format&fit=crop&q=80&w=800';

  return (
    <motion.div
      className="sanctuary-card"
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: index * 0.05 }}
      onClick={() => onClick(garden)}
    >
      <div className="card-image-container">
        <img src={photoUrl} alt={garden.name} className="card-image" />
      </div>
      <div className="card-content">
        <div className="card-header">
          <h3 className="garden-name">{garden.name}</h3>
          <span className={`status-chip ${garden.status === 'Ready' ? 'status-ready' : 'status-processing'}`}>
            {garden.status || 'New'}
          </span>
        </div>

        <p className="garden-recommendation">
          {garden.recommendation || "Our AI is analyzing your botanical sanctuary..."}
        </p>

        <div style={{ marginTop: '1.5rem', display: 'flex', alignItems: 'center', color: 'var(--color-primary)', fontSize: '0.85rem', fontWeight: '600' }}>
          Explore {garden.plants?.length || 0} plants <ChevronRight size={16} />
        </div>
      </div>
    </motion.div>
  );
};

const PlantCard = ({ plant, index }) => {
  const photoUrl = plant.image_url || 'https://images.unsplash.com/photo-1545241047-6083a3684587?auto=format&fit=crop&q=80&w=800';

  return (
    <motion.div
      className="plant-card sanctuary-card"
      initial={{ opacity: 0, x: 50 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.1 }}
    >
      <div className="card-image-container" style={{ aspectRatio: '1/1' }}>
        <img src={photoUrl} alt={plant.name} className="card-image" />
      </div>
      <div className="card-content">
        <div className="plant-variety">{plant.plant_variety || 'Unknown Species'}</div>
        <h3 className="garden-name" style={{ fontSize: '1.4rem', marginBottom: '0.5rem' }}>{plant.name}</h3>

        <div className="condition-badge">
          {plant.latest_condition || 'Healthy'}
        </div>

        <p className="garden-recommendation" style={{ marginTop: '1rem', minHeight: '4.5em' }}>
          {plant.latest_recommendation || "Maintain consistent care to ensure your plant thrives in its current environment."}
        </p>

        <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem', borderTop: '1px solid var(--color-surface-container)', paddingTop: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--color-outline)', fontSize: '0.8rem' }}>
            <Droplets size={14} /> Normal
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--color-outline)', fontSize: '0.8rem' }}>
            <Sun size={14} /> Bright
          </div>
        </div>
      </div>
    </motion.div>
  );
};

const Carousel = ({ items, renderItem, type }) => {
  const [scrollProgress, setScrollProgress] = useState(0);
  const carouselRef = React.useRef(null);

  const handleScroll = () => {
    if (carouselRef.current) {
      const { scrollLeft, scrollWidth, clientWidth } = carouselRef.current;
      const progress = (scrollLeft / (scrollWidth - clientWidth)) * 100;
      setScrollProgress(progress);
    }
  };

  return (
    <div className="garden-carousel-root">
      <div
        className="garden-carousel-container"
        ref={carouselRef}
        onScroll={handleScroll}
      >
        <AnimatePresence mode="popLayout">
          {items.map((item, index) => (
            <div key={item.id} className="carousel-card-wrapper">
              {renderItem(item, index)}
            </div>
          ))}
        </AnimatePresence>
      </div>

      {items.length > 1 && (
        <div className="progress-bar-root">
          <motion.div
            className="progress-bar-indicator"
            animate={{ width: `${scrollProgress}%` }}
            transition={{ type: 'spring', bounce: 0, duration: 0.2 }}
          />
        </div>
      )}
    </div>
  );
};

function App() {
  const [gardens, setGardens] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedGarden, setSelectedGarden] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadData, setUploadData] = useState({ name: '', photos: [] });
  const [uploadingState, setUploadingState] = useState(false);

  const fetchGardens = async () => {
    try {
      setLoading(true);
      const data = await getDetailedGardens(4);
      setGardens(data);
    } catch (err) {
      setError("Connection error. Ensure backend is running at http://localhost:8000");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGardens();
  }, []);

  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    if (!uploadData.name || uploadData.photos.length === 0) return;
    
    setUploadingState(true);
    try {
      await uploadGardenPhotos(uploadData.photos, uploadData.name, 4);
      setUploadData({ name: '', photos: [] });
      setIsUploading(false);
      await fetchGardens();
    } catch (err) {
      console.error("Upload failed", err);
      alert("Failed to upload garden. Please try again.");
    } finally {
      setUploadingState(false);
    }
  };

  if (loading && !isUploading && gardens.length === 0) {
    return (
      <div className="sanctuary-container empty-state">
        <Loader2 className="animate-spin" size={48} style={{ margin: '0 auto 1rem', color: 'var(--color-primary)' }} />
        <p>Analyzing your botanical domain...</p>
      </div>
    );
  }

  return (
    <div className="sanctuary-container">
      <AnimatePresence mode="wait">
        {isUploading ? (
          <motion.div
            key="upload-garden"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <button className="back-button" onClick={() => setIsUploading(false)}>
              <ArrowLeft size={18} /> Cancel
            </button>
            <header style={{ marginBottom: '2.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--color-primary)', marginBottom: '0.5rem' }}>
                <Leaf size={20} />
                <span style={{ fontSize: '0.9rem', fontWeight: '600', letterSpacing: '0.1em', textTransform: 'uppercase' }}>Add New Growth</span>
              </div>
              <h1 className="page-title" style={{ marginTop: '0.25rem' }}>Capture Sanctuary</h1>
            </header>

            <form onSubmit={handleUploadSubmit} className="upload-form-container">
              <div className="input-group">
                <label className="input-label">Sanctuary Name</label>
                <input
                  type="text"
                  className="text-input"
                  placeholder="e.g. Sunny Balcony, Indoor Jungle"
                  value={uploadData.name}
                  onChange={(e) => setUploadData({ ...uploadData, name: e.target.value })}
                  required
                />
              </div>

              <div className="input-group">
                <label className="input-label">Plant Photos</label>
                <label className="upload-zone" style={{ display: 'block' }}>
                  <ImageIcon size={40} className="upload-icon" />
                  <p className="upload-text">
                    {uploadData.photos.length > 0 
                      ? `${uploadData.photos.length} photos selected` 
                      : "Tap to select or drop photos"}
                  </p>
                  <p className="upload-subtext">High-res JPG or PNG works best</p>
                  <input 
                    type="file" 
                    multiple 
                    className="hidden" 
                    style={{ display: 'none' }}
                    onChange={(e) => setUploadData({ ...uploadData, photos: Array.from(e.target.files) })} 
                    accept="image/*" 
                    required 
                  />
                </label>
              </div>

              <button 
                type="submit" 
                className="btn-primary"
                disabled={uploadingState || uploadData.photos.length === 0 || !uploadData.name}
              >
                {uploadingState ? <Loader2 className="animate-spin" size={20} /> : <Sparkles size={20} />}
                {uploadingState ? 'Analyzing...' : 'Initialize AI Analysis'}
              </button>
            </form>
          </motion.div>
        ) : !selectedGarden ? (
          <motion.div
            key="gardens-list"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
          >
            <header className="header-actions" style={{ marginBottom: '3rem' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--color-primary)', marginBottom: '0.5rem' }}>
                  <Leaf size={20} />
                  <span style={{ fontSize: '0.9rem', fontWeight: '600', letterSpacing: '0.1em', textTransform: 'uppercase' }}>Botanical Manager</span>
                </div>
                <h1 className="page-title" style={{ marginBottom: 0 }}>My Sanctuaries</h1>
              </div>
              <button className="btn-icon" onClick={() => setIsUploading(true)} title="Add Garden">
                <Plus size={24} />
              </button>
            </header>
            
            {gardens.length > 0 ? (
              <Carousel
                items={gardens}
                renderItem={(garden, index) => (
                  <SanctuaryCard garden={garden} index={index} onClick={setSelectedGarden} />
                )}
              />
            ) : (
              <div className="empty-state">
                <Leaf size={48} style={{ opacity: 0.2, margin: '0 auto 1rem' }} />
                <p>No sanctuaries found. Click the + button to add one.</p>
              </div>
            )}
          </motion.div>
        ) : (
          <motion.div
            key="plants-list"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
          >
            <button className="back-button" onClick={() => setSelectedGarden(null)}>
              <ArrowLeft size={18} /> Back to Sanctuaries
            </button>
            <header style={{ marginBottom: '2.5rem' }}>
              <span style={{ fontSize: '0.9rem', fontWeight: '600', color: 'var(--color-primary)', opacity: 0.6 }}>{selectedGarden.name}</span>
              <h1 className="page-title" style={{ marginTop: '0.25rem' }}>Botanical Residents</h1>
            </header>

            {selectedGarden.plants && selectedGarden.plants.length > 0 ? (
              <Carousel
                items={selectedGarden.plants}
                renderItem={(plant, index) => (
                  <PlantCard plant={plant} index={index} />
                )}
              />
            ) : (
              <div className="empty-state">
                <Leaf size={48} style={{ opacity: 0.2, margin: '0 auto 1rem' }} />
                <p>No residents found in this sanctuary yet.</p>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default App;

