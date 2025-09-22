import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search, Filter, Download, Share2, FileText, ExternalLink, BookOpen,
  Clock, User, Star, ThumbsUp, ThumbsDown, Copy, MoreHorizontal,
  Eye, EyeOff, Bookmark, BookmarkCheck, X, RefreshCw, Sliders,
  Hash, Calendar, Folder, Tag, MessageSquare, ChevronDown, ChevronUp,
  Paperclip, Image, Video, File, Music, Code, Archive
} from 'lucide-react';

// Search Filters
const FILTER_TYPES = {
  DOCUMENT_TYPE: 'document_type',
  DATE_RANGE: 'date_range',
  SOURCE: 'source',
  TAGS: 'tags',
  SIZE: 'size',
  LANGUAGE: 'language'
};

// Sort Options
const SORT_OPTIONS = {
  RELEVANCE: 'relevance',
  DATE: 'date',
  SIZE: 'size',
  RATING: 'rating',
  VIEWS: 'views'
};

// Search Result Types
const RESULT_TYPES = {
  TEXT: 'text',
  PDF: 'pdf',
  IMAGE: 'image',
  VIDEO: 'video',
  AUDIO: 'audio',
  CODE: 'code',
  ARCHIVE: 'archive'
};

const RAGSearch = ({ onClose }) => {
  // Search State
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchHistory, setSearchHistory] = useState([]);
  const [suggestions, setSuggestions] = useState([]);

  // Filters and Sorting
  const [filters, setFilters] = useState({
    documentType: [],
    dateRange: { start: null, end: null },
    sources: [],
    tags: [],
    sizeRange: { min: 0, max: null },
    language: 'all'
  });

  const [sortBy, setSortBy] = useState(SORT_OPTIONS.RELEVANCE);
  const [sortOrder, setSortOrder] = useState('desc');
  const [showFilters, setShowFilters] = useState(false);

  // Results View
  const [viewMode, setViewMode] = useState('list'); // list, grid, detail
  const [selectedResult, setSelectedResult] = useState(null);
  const [expandedResults, setExpandedResults] = useState(new Set());

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [resultsPerPage, setResultsPerPage] = useState(10);

  // Search Stats
  const [searchStats, setSearchStats] = useState({
    totalResults: 0,
    searchTime: 0,
    queryUnderstanding: 0,
    sourcesSearched: 0
  });

  const searchInputRef = useRef(null);

  // Initialize component
  useEffect(() => {
    loadSearchHistory();
    if (searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, []);

  const loadSearchHistory = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8787/api/rag/search/history');
      if (response.ok) {
        const history = await response.json();
        setSearchHistory(history);
      }
    } catch (error) {
      console.error('Failed to load search history:', error);
    }
  }, []);

  const performSearch = useCallback(async (searchQuery, page = 1) => {
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    setCurrentPage(page);

    try {
      const searchParams = new URLSearchParams({
        q: searchQuery,
        page: page.toString(),
        per_page: resultsPerPage.toString(),
        sort: sortBy,
        order: sortOrder
      });

      // Add filters
      if (filters.documentType.length > 0) {
        searchParams.append('doc_type', filters.documentType.join(','));
      }
      if (filters.dateRange.start) {
        searchParams.append('date_from', filters.dateRange.start);
      }
      if (filters.dateRange.end) {
        searchParams.append('date_to', filters.dateRange.end);
      }
      if (filters.sources.length > 0) {
        searchParams.append('sources', filters.sources.join(','));
      }

      const startTime = Date.now();
      const response = await fetch(`http://localhost:8787/api/rag/search?${searchParams}`);
      const endTime = Date.now();

      if (response.ok) {
        const data = await response.json();
        setSearchResults(data.results);
        setSearchStats({
          totalResults: data.total,
          searchTime: endTime - startTime,
          queryUnderstanding: data.queryUnderstanding,
          sourcesSearched: data.sourcesSearched
        });

        // Add to search history
        if (page === 1) {
          addToSearchHistory(searchQuery);
        }
      }
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setIsSearching(false);
    }
  }, [filters, sortBy, sortOrder, resultsPerPage]);

  const addToSearchHistory = useCallback((query) => {
    const newHistory = [
      { query, timestamp: new Date().toISOString() },
      ...searchHistory.filter(h => h.query !== query)
    ].slice(0, 20);

    setSearchHistory(newHistory);
    localStorage.setItem('rag-search-history', JSON.stringify(newHistory));
  }, [searchHistory]);

  const getSuggestions = useCallback(async (input) => {
    if (input.length < 2) {
      setSuggestions([]);
      return;
    }

    try {
      const response = await fetch(`http://localhost:8787/api/rag/search/suggest?q=${encodeURIComponent(input)}`);
      if (response.ok) {
        const data = await response.json();
        setSuggestions(data.suggestions || []);
      }
    } catch (error) {
      console.error('Failed to get suggestions:', error);
    }
  }, []);

  const handleSearch = useCallback(() => {
    performSearch(query, 1);
  }, [query, performSearch]);

  const handleQueryChange = useCallback((value) => {
    setQuery(value);
    getSuggestions(value);
  }, [getSuggestions]);

  const handleKeyPress = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSearch();
    }
  }, [handleSearch]);

  const toggleFilter = useCallback((filterType, value) => {
    setFilters(prev => ({
      ...prev,
      [filterType]: prev[filterType].includes(value)
        ? prev[filterType].filter(f => f !== value)
        : [...prev[filterType], value]
    }));
  }, []);

  const clearFilters = useCallback(() => {
    setFilters({
      documentType: [],
      dateRange: { start: null, end: null },
      sources: [],
      tags: [],
      sizeRange: { min: 0, max: null },
      language: 'all'
    });
  }, []);

  const toggleExpandResult = useCallback((resultId) => {
    setExpandedResults(prev => {
      const newSet = new Set(prev);
      if (newSet.has(resultId)) {
        newSet.delete(resultId);
      } else {
        newSet.add(resultId);
      }
      return newSet;
    });
  }, []);

  const rateResult = useCallback(async (resultId, rating) => {
    try {
      await fetch(`http://localhost:8787/api/rag/search/rate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resultId, rating })
      });

      setSearchResults(prev => prev.map(result =>
        result.id === resultId ? { ...result, userRating: rating } : result
      ));
    } catch (error) {
      console.error('Failed to rate result:', error);
    }
  }, []);

  const exportResults = useCallback(async (format = 'json') => {
    try {
      const exportParams = new URLSearchParams({
        q: query,
        format,
        ...Object.fromEntries(Object.entries(filters).filter(([_, v]) => v.length > 0))
      });

      const response = await fetch(`http://localhost:8787/api/rag/search/export?${exportParams}`);
      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `rag-search-results-${new Date().toISOString().split('T')[0]}.${format}`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Export failed:', error);
    }
  }, [query, filters]);

  const shareResult = useCallback(async (result) => {
    try {
      await navigator.clipboard.writeText(`${window.location.origin}/rag/search?q=${result.id}`);
      alert('Share link copied to clipboard!');
    } catch (error) {
      console.error('Failed to copy share link:', error);
    }
  }, []);

  const copyResultText = useCallback(async (result) => {
    try {
      await navigator.clipboard.writeText(result.content);
      alert('Content copied to clipboard!');
    } catch (error) {
      console.error('Failed to copy content:', error);
    }
  }, []);

  const getFileIcon = (fileType) => {
    switch (fileType) {
      case RESULT_TYPES.PDF: return <File className="w-4 h-4" />;
      case RESULT_TYPES.IMAGE: return <Image className="w-4 h-4" />;
      case RESULT_TYPES.VIDEO: return <Video className="w-4 h-4" />;
      case RESULT_TYPES.AUDIO: return <Music className="w-4 h-4" />;
      case RESULT_TYPES.CODE: return <Code className="w-4 h-4" />;
      case RESULT_TYPES.ARCHIVE: return <Archive className="w-4 h-4" />;
      default: return <FileText className="w-4 h-4" />;
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days} days ago`;
    if (days < 30) return `${Math.floor(days / 7)} weeks ago`;
    return date.toLocaleDateString();
  };

  const formatRelevanceScore = (score) => {
    return Math.round(score * 100);
  };

  // Paginate results
  const totalPages = Math.ceil(searchStats.totalResults / resultsPerPage);
  const startIndex = (currentPage - 1) * resultsPerPage;
  const endIndex = startIndex + resultsPerPage;
  const paginatedResults = searchResults.slice(startIndex, endIndex);

  return (
    <div className="h-full flex flex-col bg-slate-900 text-white">
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-slate-800 border-b border-slate-700">
        <div className="flex items-center space-x-3">
          <Search className="w-6 h-6 text-blue-400" />
          <h2 className="text-xl font-semibold">RAG Search</h2>
          {searchStats.totalResults > 0 && (
            <span className="text-sm text-slate-400">
              {searchStats.totalResults.toLocaleString()} results ({searchStats.searchTime}ms)
            </span>
          )}
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => exportResults('json')}
            disabled={searchResults.length === 0}
            className="px-3 py-1 bg-slate-700 hover:bg-slate-600 disabled:bg-slate-800 rounded-lg text-sm"
          >
            <Download className="w-4 h-4 mr-1 inline" />
            Export
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`px-3 py-1 rounded-lg text-sm ${
              viewMode === 'list' ? 'bg-blue-600' : 'bg-slate-700 hover:bg-slate-600'
            }`}
          >
            List
          </button>
          <button
            onClick={() => setViewMode('grid')}
            className={`px-3 py-1 rounded-lg text-sm ${
              viewMode === 'grid' ? 'bg-blue-600' : 'bg-slate-700 hover:bg-slate-600'
            }`}
          >
            Grid
          </button>
          <button
            onClick={onClose}
            className="px-3 py-1 bg-slate-600 hover:bg-slate-700 rounded-lg text-sm"
          >
            ✕
          </button>
        </div>
      </div>

      {/* Search Interface */}
      <div className="flex-1 flex overflow-hidden">
        {/* Main Search Area */}
        <div className="flex-1 flex flex-col">
          {/* Search Bar */}
          <div className="p-4 border-b border-slate-700">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
              <textarea
                ref={searchInputRef}
                value={query}
                onChange={(e) => handleQueryChange(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Search your knowledge base..."
                className="w-full pl-12 pr-4 py-3 bg-slate-800 text-white rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none resize-none"
                rows={1}
                style={{ minHeight: '48px' }}
              />
              <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center space-x-2">
                {query && (
                  <button
                    onClick={() => setQuery('')}
                    className="p-1 text-slate-400 hover:text-white rounded"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
                <button
                  onClick={handleSearch}
                  disabled={isSearching || !query.trim()}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 rounded-lg text-sm"
                >
                  {isSearching ? <RefreshCw className="w-4 h-4 animate-spin" /> : 'Search'}
                </button>
              </div>
            </div>

            {/* Suggestions */}
            {suggestions.length > 0 && (
              <div className="absolute z-10 w-full mt-1 bg-slate-800 border border-slate-600 rounded-lg shadow-lg">
                {suggestions.map((suggestion, index) => (
                  <button
                    key={index}
                    onClick={() => {
                      setQuery(suggestion);
                      setSuggestions([]);
                    }}
                    className="w-full text-left px-4 py-2 hover:bg-slate-700 text-sm"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            )}

            {/* Quick Filters */}
            <div className="flex items-center space-x-4 mt-3 text-sm">
              <button
                onClick={() => setShowFilters(!showFilters)}
                className={`flex items-center space-x-1 px-3 py-1 rounded ${
                  showFilters ? 'bg-blue-600' : 'bg-slate-700 hover:bg-slate-600'
                }`}
              >
                <Sliders className="w-4 h-4" />
                <span>Filters</span>
                {Object.values(filters).some(f => Array.isArray(f) ? f.length > 0 : f !== 'all') && (
                  <span className="bg-red-500 text-white text-xs px-1 rounded">!</span>
                )}
              </button>

              <div className="flex items-center space-x-2">
                <span className="text-slate-400">Sort by:</span>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="bg-slate-700 text-white rounded px-2 py-1 border border-slate-600"
                >
                  {Object.entries(SORT_OPTIONS).map(([key, value]) => (
                    <option key={value} value={value}>
                      {key.replace('_', ' ').toLowerCase()}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-center space-x-2">
                <span className="text-slate-400">Order:</span>
                <select
                  value={sortOrder}
                  onChange={(e) => setSortOrder(e.target.value)}
                  className="bg-slate-700 text-white rounded px-2 py-1 border border-slate-600"
                >
                  <option value="desc">Descending</option>
                  <option value="asc">Ascending</option>
                </select>
              </div>
            </div>
          </div>

          {/* Results Area */}
          <div className="flex-1 overflow-y-auto">
            {searchResults.length === 0 && !isSearching && query ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <Search className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-white mb-2">No results found</h3>
                  <p className="text-slate-400">Try different keywords or adjust your filters</p>
                </div>
              </div>
            ) : isSearching ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <RefreshCw className="w-16 h-16 text-blue-400 animate-spin mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-white mb-2">Searching...</h3>
                  <p className="text-slate-400">Finding relevant information</p>
                </div>
              </div>
            ) : (
              <div className="p-4">
                {/* Results Header */}
                {searchStats.totalResults > 0 && (
                  <div className="flex items-center justify-between mb-4 text-sm text-slate-400">
                    <div>
                      Showing {startIndex + 1}-{Math.min(endIndex, searchStats.totalResults)} of {searchStats.totalResults.toLocaleString()} results
                    </div>
                    <div className="flex items-center space-x-4">
                      <span>Searched {searchStats.sourcesSearched} sources</span>
                      <span>Query understanding: {Math.round(searchStats.queryUnderstanding * 100)}%</span>
                    </div>
                  </div>
                )}

                {/* Results List */}
                <div className="space-y-4">
                  <AnimatePresence>
                    {paginatedResults.map(result => (
                      <motion.div
                        key={result.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden"
                      >
                        <div className="p-4">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center space-x-2 mb-2">
                                {getFileIcon(result.type)}
                                <h3 className="font-medium text-white">{result.title}</h3>
                                <span className="text-xs text-slate-400">
                                  {formatRelevanceScore(result.relevanceScore)}% match
                                </span>
                              </div>

                              <p className="text-slate-300 text-sm mb-2 line-clamp-2">
                                {result.snippet}
                              </p>

                              <div className="flex items-center space-x-4 text-xs text-slate-400">
                                <div className="flex items-center space-x-1">
                                  <FileText className="w-3 h-3" />
                                  <span>{result.documentType}</span>
                                </div>
                                <div className="flex items-center space-x-1">
                                  <Calendar className="w-3 h-3" />
                                  <span>{formatDate(result.date)}</span>
                                </div>
                                <div className="flex items-center space-x-1">
                                  <User className="w-3 h-3" />
                                  <span>{result.author}</span>
                                </div>
                                {result.size && (
                                  <div className="flex items-center space-x-1">
                                    <Hash className="w-3 h-3" />
                                    <span>{result.size}</span>
                                  </div>
                                )}
                              </div>

                              {result.tags && result.tags.length > 0 && (
                                <div className="flex items-center space-x-2 mt-2">
                                  <Tag className="w-3 h-3 text-slate-400" />
                                  <div className="flex flex-wrap gap-1">
                                    {result.tags.slice(0, 5).map(tag => (
                                      <span key={tag} className="text-xs bg-slate-700 text-slate-300 px-2 py-1 rounded">
                                        {tag}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>

                            <div className="flex items-center space-x-2 ml-4">
                              <button
                                onClick={() => toggleExpandResult(result.id)}
                                className="p-1 text-slate-400 hover:text-white rounded"
                              >
                                {expandedResults.has(result.id) ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                              </button>
                              <button
                                onClick={() => copyResultText(result)}
                                className="p-1 text-slate-400 hover:text-white rounded"
                              >
                                <Copy className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => shareResult(result)}
                                className="p-1 text-slate-400 hover:text-white rounded"
                              >
                                <Share2 className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => window.open(result.url, '_blank')}
                                className="p-1 text-slate-400 hover:text-white rounded"
                              >
                                <ExternalLink className="w-4 h-4" />
                              </button>
                            </div>
                          </div>

                          {/* Expanded Content */}
                          {expandedResults.has(result.id) && (
                            <div className="mt-4 pt-4 border-t border-slate-700">
                              <div className="text-slate-300 text-sm mb-4 whitespace-pre-wrap">
                                {result.content}
                              </div>

                              <div className="flex items-center justify-between">
                                <div className="flex items-center space-x-2">
                                  <span className="text-xs text-slate-400">Rate this result:</span>
                                  <button
                                    onClick={() => rateResult(result.id, 'positive')}
                                    className={`p-1 rounded ${
                                      result.userRating === 'positive' ? 'text-green-400 bg-green-400/20' : 'text-slate-400 hover:text-green-400'
                                    }`}
                                  >
                                    <ThumbsUp className="w-4 h-4" />
                                  </button>
                                  <button
                                    onClick={() => rateResult(result.id, 'negative')}
                                    className={`p-1 rounded ${
                                      result.userRating === 'negative' ? 'text-red-400 bg-red-400/20' : 'text-slate-400 hover:text-red-400'
                                    }`}
                                  >
                                    <ThumbsDown className="w-4 h-4" />
                                  </button>
                                </div>

                                <div className="flex items-center space-x-2 text-xs text-slate-400">
                                  <Star className="w-3 h-3" />
                                  <span>{result.views || 0} views</span>
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="flex items-center justify-center mt-6 space-x-2">
                    <button
                      onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                      disabled={currentPage === 1}
                      className="px-3 py-1 bg-slate-700 disabled:bg-slate-800 rounded-lg text-sm"
                    >
                      Previous
                    </button>
                    <div className="flex items-center space-x-1">
                      {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                        const page = Math.max(1, Math.min(totalPages - 4, currentPage - 2)) + i;
                        return (
                          <button
                            key={page}
                            onClick={() => setCurrentPage(page)}
                            className={`px-3 py-1 rounded-lg text-sm ${
                              currentPage === page ? 'bg-blue-600' : 'bg-slate-700 hover:bg-slate-600'
                            }`}
                          >
                            {page}
                          </button>
                        );
                      })}
                    </div>
                    <button
                      onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                      disabled={currentPage === totalPages}
                      className="px-3 py-1 bg-slate-700 disabled:bg-slate-800 rounded-lg text-sm"
                    >
                      Next
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Filters Sidebar */}
        {showFilters && (
          <div className="w-80 bg-slate-800 border-l border-slate-700 p-4 overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-medium text-white">Filters</h3>
              <button
                onClick={clearFilters}
                className="text-sm text-slate-400 hover:text-white"
              >
                Clear all
              </button>
            </div>

            {/* Document Type Filter */}
            <div className="mb-6">
              <h4 className="text-sm font-medium text-white mb-2">Document Type</h4>
              <div className="space-y-2">
                {Object.values(RESULT_TYPES).map(type => (
                  <label key={type} className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={filters.documentType.includes(type)}
                      onChange={() => toggleFilter('documentType', type)}
                      className="rounded text-blue-600"
                    />
                    <span className="text-sm text-slate-300 capitalize">{type}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Date Range Filter */}
            <div className="mb-6">
              <h4 className="text-sm font-medium text-white mb-2">Date Range</h4>
              <div className="space-y-2">
                <div>
                  <label className="text-xs text-slate-400">From</label>
                  <input
                    type="date"
                    value={filters.dateRange.start || ''}
                    onChange={(e) => setFilters(prev => ({
                      ...prev,
                      dateRange: { ...prev.dateRange, start: e.target.value }
                    }))}
                    className="w-full bg-slate-700 text-white rounded px-2 py-1 text-sm border border-slate-600"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400">To</label>
                  <input
                    type="date"
                    value={filters.dateRange.end || ''}
                    onChange={(e) => setFilters(prev => ({
                      ...prev,
                      dateRange: { ...prev.dateRange, end: e.target.value }
                    }))}
                    className="w-full bg-slate-700 text-white rounded px-2 py-1 text-sm border border-slate-600"
                  />
                </div>
              </div>
            </div>

            {/* Source Filter */}
            <div className="mb-6">
              <h4 className="text-sm font-medium text-white mb-2">Sources</h4>
              <div className="space-y-2">
                {['Local Documents', 'Web Pages', 'Databases', 'APIs'].map(source => (
                  <label key={source} className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={filters.sources.includes(source)}
                      onChange={() => toggleFilter('sources', source)}
                      className="rounded text-blue-600"
                    />
                    <span className="text-sm text-slate-300">{source}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Size Range Filter */}
            <div className="mb-6">
              <h4 className="text-sm font-medium text-white mb-2">Size Range</h4>
              <div className="space-y-2">
                <div>
                  <label className="text-xs text-slate-400">Min Size (KB)</label>
                  <input
                    type="number"
                    value={filters.sizeRange.min}
                    onChange={(e) => setFilters(prev => ({
                      ...prev,
                      sizeRange: { ...prev.sizeRange, min: parseInt(e.target.value) || 0 }
                    }))}
                    className="w-full bg-slate-700 text-white rounded px-2 py-1 text-sm border border-slate-600"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400">Max Size (KB)</label>
                  <input
                    type="number"
                    value={filters.sizeRange.max || ''}
                    onChange={(e) => setFilters(prev => ({
                      ...prev,
                      sizeRange: { ...prev.sizeRange, max: parseInt(e.target.value) || null }
                    }))}
                    className="w-full bg-slate-700 text-white rounded px-2 py-1 text-sm border border-slate-600"
                  />
                </div>
              </div>
            </div>

            {/* Language Filter */}
            <div className="mb-6">
              <h4 className="text-sm font-medium text-white mb-2">Language</h4>
              <select
                value={filters.language}
                onChange={(e) => setFilters(prev => ({ ...prev, language: e.target.value }))}
                className="w-full bg-slate-700 text-white rounded px-2 py-1 text-sm border border-slate-600"
              >
                <option value="all">All Languages</option>
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
                <option value="de">German</option>
                <option value="zh">Chinese</option>
                <option value="ja">Japanese</option>
              </select>
            </div>

            {/* Active Filters Summary */}
            {Object.values(filters).some(f => Array.isArray(f) ? f.length > 0 : f !== 'all') && (
              <div className="mt-6 p-3 bg-slate-700 rounded-lg">
                <h4 className="text-sm font-medium text-white mb-2">Active Filters</h4>
                <div className="space-y-1 text-xs">
                  {filters.documentType.length > 0 && (
                    <div className="flex items-center justify-between">
                      <span className="text-slate-300">Document types:</span>
                      <span className="text-white">{filters.documentType.join(', ')}</span>
                    </div>
                  )}
                  {filters.sources.length > 0 && (
                    <div className="flex items-center justify-between">
                      <span className="text-slate-300">Sources:</span>
                      <span className="text-white">{filters.sources.join(', ')}</span>
                    </div>
                  )}
                  {filters.language !== 'all' && (
                    <div className="flex items-center justify-between">
                      <span className="text-slate-300">Language:</span>
                      <span className="text-white">{filters.language}</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Search History Sidebar */}
        {searchHistory.length > 0 && !showFilters && (
          <div className="w-64 bg-slate-800 border-l border-slate-700 p-4">
            <h3 className="font-medium text-white mb-4">Recent Searches</h3>
            <div className="space-y-2">
              {searchHistory.slice(0, 10).map((item, index) => (
                <button
                  key={index}
                  onClick={() => {
                    setQuery(item.query);
                    performSearch(item.query, 1);
                  }}
                  className="w-full text-left p-2 bg-slate-700 hover:bg-slate-600 rounded text-sm"
                >
                  <div className="text-white truncate">{item.query}</div>
                  <div className="text-xs text-slate-400">{formatDate(item.timestamp)}</div>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default RAGSearch;