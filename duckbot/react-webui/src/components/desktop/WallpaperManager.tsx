import React, { useState, useRef, useEffect } from 'react';

interface Wallpaper {
  id: string;
  name: string;
  url: string;
  category: string;
  isCustom?: boolean;
  thumbnail?: string;
}

interface WallpaperCategory {
  id: string;
  name: string;
  icon: string;
  color: string;
}

interface WallpaperManagerProps {
  isVisible: boolean;
  onClose: () => void;
  onWallpaperSelect: (wallpaper: Wallpaper) => void;
  currentWallpaper?: string;
}

const WallpaperManager: React.FC<WallpaperManagerProps> = ({
  isVisible,
  onClose,
  onWallpaperSelect,
  currentWallpaper
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [customWallpapers, setCustomWallpapers] = useState<Wallpaper[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  const categories: WallpaperCategory[] = [
    { id: 'all', name: 'All', icon: '🎨', color: 'bg-gradient-to-r from-purple-500 to-pink-500' },
    { id: 'abstract', name: 'Abstract', icon: '🌈', color: 'bg-gradient-to-r from-blue-500 to-purple-500' },
    { id: 'nature', name: 'Nature', icon: '🌿', color: 'bg-gradient-to-r from-green-500 to-blue-500' },
    { id: 'city', name: 'City', icon: '🏙️', color: 'bg-gradient-to-r from-gray-500 to-blue-500' },
    { id: 'space', name: 'Space', icon: '🌌', color: 'bg-gradient-to-r from-indigo-500 to-purple-500' },
    { id: 'minimal', name: 'Minimal', icon: '✨', color: 'bg-gradient-to-r from-gray-400 to-gray-600' },
    { id: 'technology', name: 'Technology', icon: '💻', color: 'bg-gradient-to-r from-cyan-500 to-blue-500' },
    { id: 'art', name: 'Art', icon: '🎭', color: 'bg-gradient-to-r from-pink-500 to-red-500' }
  ];

  const predefinedWallpapers: Wallpaper[] = [
    // Abstract
    { id: 'abstract-1', name: 'Cosmic Flow', url: 'https://picsum.photos/1920/1080?random=1&blur=1', category: 'abstract', thumbnail: 'https://picsum.photos/200/150?random=1&blur=1' },
    { id: 'abstract-2', name: 'Neon Dreams', url: 'https://picsum.photos/1920/1080?random=2&blur=1', category: 'abstract', thumbnail: 'https://picsum.photos/200/150?random=2&blur=1' },
    { id: 'abstract-3', name: 'Geometric Harmony', url: 'https://picsum.photos/1920/1080?random=3&blur=1', category: 'abstract', thumbnail: 'https://picsum.photos/200/150?random=3&blur=1' },
    { id: 'abstract-4', name: 'Fluid Dynamics', url: 'https://picsum.photos/1920/1080?random=4&blur=1', category: 'abstract', thumbnail: 'https://picsum.photos/200/150?random=4&blur=1' },

    // Nature
    { id: 'nature-1', name: 'Mountain Serenity', url: 'https://picsum.photos/1920/1080?random=5&blur=1', category: 'nature', thumbnail: 'https://picsum.photos/200/150?random=5&blur=1' },
    { id: 'nature-2', name: 'Forest Mist', url: 'https://picsum.photos/1920/1080?random=6&blur=1', category: 'nature', thumbnail: 'https://picsum.photos/200/150?random=6&blur=1' },
    { id: 'nature-3', name: 'Ocean Waves', url: 'https://picsum.photos/1920/1080?random=7&blur=1', category: 'nature', thumbnail: 'https://picsum.photos/200/150?random=7&blur=1' },
    { id: 'nature-4', name: 'Desert Sunset', url: 'https://picsum.photos/1920/1080?random=8&blur=1', category: 'nature', thumbnail: 'https://picsum.photos/200/150?random=8&blur=1' },

    // City
    { id: 'city-1', name: 'Skyline Nights', url: 'https://picsum.photos/1920/1080?random=9&blur=1', category: 'city', thumbnail: 'https://picsum.photos/200/150?random=9&blur=1' },
    { id: 'city-2', name: 'Urban Jungle', url: 'https://picsum.photos/1920/1080?random=10&blur=1', category: 'city', thumbnail: 'https://picsum.photos/200/150?random=10&blur=1' },
    { id: 'city-3', name: 'Metropolis', url: 'https://picsum.photos/1920/1080?random=11&blur=1', category: 'city', thumbnail: 'https://picsum.photos/200/150?random=11&blur=1' },
    { id: 'city-4', name: 'City Lights', url: 'https://picsum.photos/1920/1080?random=12&blur=1', category: 'city', thumbnail: 'https://picsum.photos/200/150?random=12&blur=1' },

    // Space
    { id: 'space-1', name: 'Galaxy Core', url: 'https://picsum.photos/1920/1080?random=13&blur=1', category: 'space', thumbnail: 'https://picsum.photos/200/150?random=13&blur=1' },
    { id: 'space-2', name: 'Nebula Dreams', url: 'https://picsum.photos/1920/1080?random=14&blur=1', category: 'space', thumbnail: 'https://picsum.photos/200/150?random=14&blur=1' },
    { id: 'space-3', name: 'Starfield', url: 'https://picsum.photos/1920/1080?random=15&blur=1', category: 'space', thumbnail: 'https://picsum.photos/200/150?random=15&blur=1' },
    { id: 'space-4', name: 'Aurora', url: 'https://picsum.photos/1920/1080?random=16&blur=1', category: 'space', thumbnail: 'https://picsum.photos/200/150?random=16&blur=1' },

    // Minimal
    { id: 'minimal-1', name: 'Clean White', url: 'https://picsum.photos/1920/1080?grayscale&blur=1', category: 'minimal', thumbnail: 'https://picsum.photos/200/150?grayscale&blur=1' },
    { id: 'minimal-2', name: 'Dark Mode', url: 'https://picsum.photos/1920/1080?grayscale&blur=1&seed=dark', category: 'minimal', thumbnail: 'https://picsum.photos/200/150?grayscale&blur=1&seed=dark' },
    { id: 'minimal-3', name: 'Gradient', url: 'https://picsum.photos/1920/1080?blur=1&seed=gradient', category: 'minimal', thumbnail: 'https://picsum.photos/200/150?blur=1&seed=gradient' },
    { id: 'minimal-4', name: 'Simple Grid', url: 'https://picsum.photos/1920/1080?blur=1&seed=grid', category: 'minimal', thumbnail: 'https://picsum.photos/200/150?blur=1&seed=grid' },

    // Technology
    { id: 'tech-1', name: 'Circuit Board', url: 'https://picsum.photos/1920/1080?random=17&blur=1', category: 'technology', thumbnail: 'https://picsum.photos/200/150?random=17&blur=1' },
    { id: 'tech-2', name: 'Digital Matrix', url: 'https://picsum.photos/1920/1080?random=18&blur=1', category: 'technology', thumbnail: 'https://picsum.photos/200/150?random=18&blur=1' },
    { id: 'tech-3', name: 'Cyberpunk', url: 'https://picsum.photos/1920/1080?random=19&blur=1', category: 'technology', thumbnail: 'https://picsum.photos/200/150?random=19&blur=1' },
    { id: 'tech-4', name: 'Holographic', url: 'https://picsum.photos/1920/1080?random=20&blur=1', category: 'technology', thumbnail: 'https://picsum.photos/200/150?random=20&blur=1' },

    // Art
    { id: 'art-1', name: 'Watercolor', url: 'https://picsum.photos/1920/1080?random=21&blur=1', category: 'art', thumbnail: 'https://picsum.photos/200/150?random=21&blur=1' },
    { id: 'art-2', name: 'Oil Painting', url: 'https://picsum.photos/1920/1080?random=22&blur=1', category: 'art', thumbnail: 'https://picsum.photos/200/150?random=22&blur=1' },
    { id: 'art-3', name: 'Digital Art', url: 'https://picsum.photos/1920/1080?random=23&blur=1', category: 'art', thumbnail: 'https://picsum.photos/200/150?random=23&blur=1' },
    { id: 'art-4', name: 'Sculpture', url: 'https://picsum.photos/1920/1080?random=24&blur=1', category: 'art', thumbnail: 'https://picsum.photos/200/150?random=24&blur=1' }
  ];

  // Load custom wallpapers from localStorage on mount
  useEffect(() => {
    const savedCustomWallpapers = localStorage.getItem('duckbot-wallpaper-custom');
    if (savedCustomWallpapers) {
      try {
        setCustomWallpapers(JSON.parse(savedCustomWallpapers));
      } catch (error) {
        console.error('Error loading custom wallpapers:', error);
      }
    }
  }, []);

  // Save custom wallpapers to localStorage when they change
  useEffect(() => {
    localStorage.setItem('duckbot-wallpaper-custom', JSON.stringify(customWallpapers));
  }, [customWallpapers]);

  const allWallpapers = [...predefinedWallpapers, ...customWallpapers];

  const filteredWallpapers = allWallpapers.filter(wallpaper => {
    const matchesCategory = selectedCategory === 'all' || wallpaper.category === selectedCategory;
    const matchesSearch = wallpaper.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         wallpaper.category.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      alert('Please select an image file');
      return;
    }

    setIsUploading(true);
    try {
      const reader = new FileReader();
      reader.onload = (e) => {
        const imageUrl = e.target?.result as string;
        const newWallpaper: Wallpaper = {
          id: `custom-${Date.now()}`,
          name: file.name.replace(/\.[^/.]+$/, ''),
          url: imageUrl,
          category: 'custom',
          isCustom: true,
          thumbnail: imageUrl
        };

        setCustomWallpapers(prev => [...prev, newWallpaper]);
        setIsUploading(false);

        // Show success message
        showNotification('Wallpaper uploaded successfully!', 'success');
      };
      reader.readAsDataURL(file);
    } catch (error) {
      console.error('Error uploading wallpaper:', error);
      setIsUploading(false);
      showNotification('Error uploading wallpaper', 'error');
    }
  };

  const handleWallpaperSelect = (wallpaper: Wallpaper) => {
    onWallpaperSelect(wallpaper);

    // Save to localStorage for persistence
    localStorage.setItem('duckbot-wallpaper-current', JSON.stringify({
      id: wallpaper.id,
      url: wallpaper.url,
      name: wallpaper.name,
      category: wallpaper.category,
      isCustom: wallpaper.isCustom
    }));

    // Show notification
    showNotification(`Wallpaper "${wallpaper.name}" applied`, 'success');
  };

  const showNotification = (message: string, type: 'success' | 'error') => {
    // Create a simple notification
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 px-4 py-2 rounded-lg text-white z-50 ${
      type === 'success' ? 'bg-green-500' : 'bg-red-500'
    }`;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
      notification.remove();
    }, 3000);
  };

  const handleDeleteCustomWallpaper = (wallpaperId: string, event: React.MouseEvent) => {
    event.stopPropagation();

    if (window.confirm('Are you sure you want to delete this wallpaper?')) {
      setCustomWallpapers(prev => prev.filter(wp => wp.id !== wallpaperId));
      showNotification('Wallpaper deleted', 'success');
    }
  };

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[2000] flex items-center justify-center p-4">
      <div className="bg-gray-800/95 backdrop-blur-xl rounded-2xl w-full max-w-6xl h-full max-h-[80vh] overflow-hidden border border-gray-700/50">
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-700/50">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center">
                <span className="text-white text-lg">🖼️</span>
              </div>
              <div>
                <h2 className="text-xl font-bold text-white">Wallpaper Manager</h2>
                <p className="text-sm text-gray-400">Choose your perfect desktop background</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="w-8 h-8 rounded-lg bg-gray-700/50 hover:bg-gray-700/80 flex items-center justify-center transition-colors"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-300" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
          </div>

          {/* Controls */}
          <div className="p-6 border-b border-gray-700/50 space-y-4">
            {/* Search and Upload */}
            <div className="flex items-center gap-4">
              <div className="flex-1 relative">
                <svg xmlns="http://www.w3.org/2000/svg" className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
                </svg>
                <input
                  type="text"
                  placeholder="Search wallpapers..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-gray-700/50 border border-gray-600/50 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading}
                className="px-4 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-blue-500/50 rounded-lg text-white font-medium transition-colors flex items-center gap-2"
              >
                {isUploading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
                    </svg>
                    Upload Custom
                  </>
                )}
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleFileUpload}
                className="hidden"
              />
            </div>

            {/* Categories */}
            <div className="flex flex-wrap gap-2">
              {categories.map(category => (
                <button
                  key={category.id}
                  onClick={() => setSelectedCategory(category.id)}
                  className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all flex items-center gap-2 ${
                    selectedCategory === category.id
                      ? `${category.color} text-white shadow-lg`
                      : 'bg-gray-700/50 text-gray-300 hover:bg-gray-700/80'
                  }`}
                >
                  <span>{category.icon}</span>
                  {category.name}
                </button>
              ))}
            </div>
          </div>

          {/* Wallpaper Grid */}
          <div className="flex-1 overflow-y-auto p-6">
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
              {filteredWallpapers.map(wallpaper => (
                <div
                  key={wallpaper.id}
                  onClick={() => handleWallpaperSelect(wallpaper)}
                  className={`relative group cursor-pointer rounded-lg overflow-hidden border-2 transition-all hover:scale-105 ${
                    currentWallpaper === wallpaper.url
                      ? 'border-blue-500 shadow-lg shadow-blue-500/25'
                      : 'border-gray-700/50 hover:border-gray-600'
                  }`}
                >
                  <img
                    src={wallpaper.thumbnail || wallpaper.url}
                    alt={wallpaper.name}
                    className="w-full h-32 object-cover"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
                  <div className="absolute bottom-0 left-0 right-0 p-3">
                    <h3 className="text-white text-sm font-medium truncate">{wallpaper.name}</h3>
                    <p className="text-gray-300 text-xs truncate">{wallpaper.category}</p>
                  </div>

                  {/* Custom wallpaper delete button */}
                  {wallpaper.isCustom && (
                    <button
                      onClick={(e) => handleDeleteCustomWallpaper(wallpaper.id, e)}
                      className="absolute top-2 right-2 w-6 h-6 bg-red-500/80 hover:bg-red-500 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3 text-white" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                      </svg>
                    </button>
                  )}

                  {/* Current wallpaper indicator */}
                  {currentWallpaper === wallpaper.url && (
                    <div className="absolute top-2 left-2 w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3 text-white" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {filteredWallpapers.length === 0 && (
              <div className="flex flex-col items-center justify-center h-64 text-gray-400">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 mb-4" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" />
                </svg>
                <p className="text-lg font-medium">No wallpapers found</p>
                <p className="text-sm">Try adjusting your search or category filter</p>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-gray-700/50 bg-gray-800/50">
            <div className="flex items-center justify-between text-sm text-gray-400">
              <span>{filteredWallpapers.length} wallpapers</span>
              <span>Click any wallpaper to apply it to your desktop</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WallpaperManager;