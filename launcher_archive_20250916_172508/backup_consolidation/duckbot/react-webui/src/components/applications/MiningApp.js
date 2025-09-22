import React, { useState, useEffect, useCallback } from 'react';
import { MiningService } from '../../services/miningService';

interface MiningAppProps {
    miningService: MiningService;
    onClose: () => void;
}

const MiningApp: React.FC<MiningAppProps> = ({ miningService, onClose }) => {
    const [miningStatus, setMiningStatus] = useState<any>(null);
    const [profitabilityData, setProfitabilityData] = useState<any>(null);
    const [optimizationData, setOptimizationData] = useState<any>(null);
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);
    const [selectedSoftware, setSelectedSoftware] = useState<string>('multipoolminer');
    const [selectedAlgorithm, setSelectedAlgorithm] = useState<string>('');
    const [selectedCoin, setSelectedCoin] = useState<string>('');
    const [intensity, setIntensity] = useState<number>(100);

    const fetchMiningStatus = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            const status = await miningService.getMiningStatus();
            if (status.success) {
                setMiningStatus(status.data);
            } else {
                setError(status.error || 'Failed to fetch mining status');
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setLoading(false);
        }
    }, [miningService]);

    const fetchProfitabilityData = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await miningService.getProfitabilityData();
            if (data.success) {
                setProfitabilityData(data.data);
            } else {
                setError(data.error || 'Failed to fetch profitability data');
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setLoading(false);
        }
    }, [miningService]);

    const startMining = async () => {
        try {
            setLoading(true);
            setError(null);
            const result = await miningService.startMining(
                selectedSoftware,
                selectedAlgorithm || undefined,
                selectedCoin || undefined,
                intensity
            );
            if (result.success) {
                await fetchMiningStatus();
            } else {
                setError(result.error || 'Failed to start mining');
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setLoading(false);
        }
    };

    const stopMining = async () => {
        try {
            setLoading(true);
            setError(null);
            const result = await miningService.stopMining();
            if (result.success) {
                await fetchMiningStatus();
            } else {
                setError(result.error || 'Failed to stop mining');
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setLoading(false);
        }
    };

    const optimizeMining = async () => {
        try {
            setLoading(true);
            setError(null);
            const result = await miningService.optimizeMining();
            if (result.success) {
                setOptimizationData(result.data);
            } else {
                setError(result.error || 'Failed to optimize mining');
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setLoading(false);
        }
    };

    const switchMiner = async (software: string) => {
        try {
            setLoading(true);
            setError(null);
            const result = await miningService.switchMiner(software);
            if (result.success) {
                await fetchMiningStatus();
            } else {
                setError(result.error || 'Failed to switch miner');
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchMiningStatus();
        fetchProfitabilityData();
        const interval = setInterval(() => {
            fetchMiningStatus();
        }, 30000); // Refresh every 30 seconds

        return () => clearInterval(interval);
    }, [fetchMiningStatus, fetchProfitabilityData]);

    const renderMiningStatus = () => {
        if (!miningStatus) return null;

        return (
            <div className="bg-gray-800 rounded-lg p-4 mb-4">
                <h3 className="text-lg font-semibold mb-2">Mining Status</h3>
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <p className="text-gray-400">Active Miner</p>
                        <p className="font-mono">{miningStatus.active_miner || 'None'}</p>
                    </div>
                    <div>
                        <p className="text-gray-400">Overall Status</p>
                        <p className={`font-mono ${miningStatus.overall_status === 'running' ? 'text-green-400' : 'text-red-400'}`}>
                            {miningStatus.overall_status}
                        </p>
                    </div>
                    {miningStatus.active_miner && miningStatus.miners[miningStatus.active_miner]?.stats && (
                        <>
                            <div>
                                <p className="text-gray-400">Hashrate</p>
                                <p className="font-mono">
                                    {miningStatus.miners[miningStatus.active_miner].stats.hashrate?.toLocaleString() || 0} H/s
                                </p>
                            </div>
                            <div>
                                <p className="text-gray-400">Power Consumption</p>
                                <p className="font-mono">
                                    {miningStatus.miners[miningStatus.active_miner].stats.power_consumption || 0}W
                                </p>
                            </div>
                            <div>
                                <p className="text-gray-400">Algorithm</p>
                                <p className="font-mono">{miningStatus.miners[miningStatus.active_miner].stats.algorithm || 'Unknown'}</p>
                            </div>
                            <div>
                                <p className="text-gray-400">Coin</p>
                                <p className="font-mono">{miningStatus.miners[miningStatus.active_miner].stats.coin || 'Unknown'}</p>
                            </div>
                        </>
                    )}
                </div>
            </div>
        );
    };

    const renderProfitabilityData = () => {
        if (!profitabilityData) return null;

        const algorithms = profitabilityData.algorithms || {};
        const sortedAlgorithms = Object.entries(algorithms).sort((a, b) => 
            (b[1] as any).profitability - (a[1] as any).profitability
        );

        return (
            <div className="bg-gray-800 rounded-lg p-4 mb-4">
                <h3 className="text-lg font-semibold mb-2">Algorithm Profitability</h3>
                <div className="space-y-2">
                    {sortedAlgorithms.slice(0, 5).map(([algo, data]: [string, any]) => (
                        <div key={algo} className="flex justify-between items-center">
                            <span className="font-mono">{algo.toUpperCase()} ({data.coin})</span>
                            <span className="font-mono">${data.profitability?.toFixed(4)}/day</span>
                        </div>
                    ))}
                </div>
            </div>
        );
    };

    const renderOptimizationData = () => {
        if (!optimizationData) return null;

        return (
            <div className="bg-gray-800 rounded-lg p-4 mb-4">
                <h3 className="text-lg font-semibold mb-2">Optimization Recommendations</h3>
                <div className="space-y-2">
                    <div>
                        <p className="text-gray-400">Current Software</p>
                        <p className="font-mono">{optimizationData.current_software}</p>
                    </div>
                    <div>
                        <p className="text-gray-400">Current Hashrate</p>
                        <p className="font-mono">{optimizationData.current_hashrate?.toLocaleString() || 0} H/s</p>
                    </div>
                    {optimizationData.algorithm_recommendations?.length > 0 && (
                        <div>
                            <p className="text-gray-400">Best Algorithm</p>
                            <p className="font-mono">
                                {optimizationData.algorithm_recommendations[0].algorithm?.toUpperCase()} - 
                                ${optimizationData.algorithm_recommendations[0].profitability?.toFixed(4)}/day
                            </p>
                        </div>
                    )}
                </div>
            </div>
        );
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
            <div className="bg-gray-900 rounded-lg shadow-xl w-full max-w-4xl h-5/6 overflow-hidden flex flex-col">
                {/* Header */}
                <div className="bg-gray-800 px-6 py-4 border-b border-gray-700 flex justify-between items-center">
                    <h2 className="text-xl font-bold flex items-center">
                        <span className="mr-2">⛏️</span>
                        Cryptocurrency Mining
                    </h2>
                    <button 
                        onClick={onClose}
                        className="text-gray-400 hover:text-white transition-colors"
                    >
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6">
                    {error && (
                        <div className="bg-red-900 border border-red-700 rounded-lg p-4 mb-4">
                            <p className="text-red-200">{error}</p>
                        </div>
                    )}

                    {/* Controls */}
                    <div className="bg-gray-800 rounded-lg p-4 mb-4">
                        <h3 className="text-lg font-semibold mb-3">Mining Controls</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                            <div>
                                <label className="block text-sm font-medium mb-1">Mining Software</label>
                                <select
                                    value={selectedSoftware}
                                    onChange={(e) => setSelectedSoftware(e.target.value)}
                                    className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-white"
                                    disabled={loading}
                                >
                                    <option value="multipoolminer">MultiPoolMiner</option>
                                    <option value="nplusminer">NPlusMiner</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium mb-1">Intensity (1-100)</label>
                                <input
                                    type="number"
                                    min="1"
                                    max="100"
                                    value={intensity}
                                    onChange={(e) => setIntensity(Math.min(100, Math.max(1, parseInt(e.target.value) || 100)))}
                                    className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-white"
                                    disabled={loading}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium mb-1">Algorithm (optional)</label>
                                <input
                                    type="text"
                                    value={selectedAlgorithm}
                                    onChange={(e) => setSelectedAlgorithm(e.target.value)}
                                    placeholder="e.g., kawpow"
                                    className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-white"
                                    disabled={loading}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium mb-1">Coin (optional)</label>
                                <input
                                    type="text"
                                    value={selectedCoin}
                                    onChange={(e) => setSelectedCoin(e.target.value)}
                                    placeholder="e.g., RVN"
                                    className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-white"
                                    disabled={loading}
                                />
                            </div>
                        </div>
                        <div className="flex flex-wrap gap-2">
                            <button
                                onClick={startMining}
                                disabled={loading}
                                className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 rounded-md transition-colors flex items-center"
                            >
                                {loading ? (
                                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                ) : (
                                    <span className="mr-1">▶️</span>
                                )}
                                Start Mining
                            </button>
                            <button
                                onClick={stopMining}
                                disabled={loading}
                                className="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 rounded-md transition-colors flex items-center"
                            >
                                {loading ? (
                                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                ) : (
                                    <span className="mr-1">⏹️</span>
                                )}
                                Stop Mining
                            </button>
                            <button
                                onClick={optimizeMining}
                                disabled={loading}
                                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded-md transition-colors flex items-center"
                            >
                                {loading ? (
                                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                ) : (
                                    <span className="mr-1">⚡</span>
                                )}
                                Optimize
                            </button>
                            <button
                                onClick={() => switchMiner(selectedSoftware === 'multipoolminer' ? 'nplusminer' : 'multipoolminer')}
                                disabled={loading}
                                className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 rounded-md transition-colors flex items-center"
                            >
                                {loading ? (
                                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                ) : (
                                    <span className="mr-1">🔄</span>
                                )}
                                Switch Miner
                            </button>
                            <button
                                onClick={fetchMiningStatus}
                                disabled={loading}
                                className="px-4 py-2 bg-gray-600 hover:bg-gray-700 disabled:bg-gray-600 rounded-md transition-colors flex items-center"
                            >
                                {loading ? (
                                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                ) : (
                                    <span className="mr-1">🔄</span>
                                )}
                                Refresh
                            </button>
                        </div>
                    </div>

                    {/* Status and Data */}
                    {renderMiningStatus()}
                    {renderProfitabilityData()}
                    {renderOptimizationData()}

                    {/* Loading indicator */}
                    {loading && (
                        <div className="flex justify-center items-center py-8">
                            <svg className="animate-spin h-8 w-8 text-teal-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default MiningApp;