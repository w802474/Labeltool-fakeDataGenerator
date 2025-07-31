import React from 'react';
import { clsx } from 'clsx';

interface LaserScanAnimationProps {
  isActive: boolean;
  className?: string;
  progress?: number; // 0-100
  stage?: 'starting' | 'processing' | 'finalizing';
}

export const LaserScanAnimation: React.FC<LaserScanAnimationProps> = ({ 
  isActive, 
  className,
  progress = 0,
  stage = 'processing'
}) => {
  if (!isActive) return null;

  const getStageInfo = () => {
    switch (stage) {
      case 'starting':
        return { 
          progressColor: 'from-blue-400 to-blue-600',
          glowColor: '#3b82f6',
          laserColor: '#f1f5f9' // slate-100
        };
      case 'processing':
        return { 
          progressColor: 'from-green-400 to-green-600',
          glowColor: '#10b981',
          laserColor: '#f8fafc' // slate-50
        };
      case 'finalizing':
        return { 
          progressColor: 'from-purple-400 to-purple-600',
          glowColor: '#8b5cf6',
          laserColor: '#ffffff' // white
        };
      default:
        return { 
          progressColor: 'from-blue-400 to-blue-600',
          glowColor: '#3b82f6',
          laserColor: '#f1f5f9' // slate-100
        };
    }
  };

  const stageInfo = getStageInfo();

  return (
    <div className={clsx(
      'absolute inset-0 z-50',
      'flex items-center justify-center',
      className
    )}>
      {/* Background overlay */}
      <div className="absolute inset-0 bg-black/40" />
      
      {/* Simple laser scanning effect - above the overlay */}
      <div className="absolute inset-0 overflow-hidden z-10">
        {/* Single laser beam */}
        <div 
          className="absolute w-full h-0.5"
          style={{
            background: `linear-gradient(90deg, 
              transparent 0%, 
              transparent 20%, 
              ${stageInfo.laserColor} 45%, 
              ${stageInfo.laserColor} 50%, 
              ${stageInfo.laserColor} 55%, 
              transparent 80%, 
              transparent 100%
            )`,
            boxShadow: `
              0 0 8px ${stageInfo.laserColor},
              0 0 16px ${stageInfo.laserColor},
              0 0 24px ${stageInfo.laserColor}
            `,
            animation: 'laserSweep 2s ease-in-out infinite',
          }}
        />
      </div>

      {/* Professional progress panel */}
      <div className="relative z-20">
        <div className="mx-auto px-8 py-6 bg-gray-900/90 backdrop-blur-md rounded-lg border border-gray-700/50 shadow-2xl">
          <div className="w-80">
            {/* Progress label */}
            <div className="flex justify-between items-center mb-3">
              <span className="text-sm font-medium text-gray-300">Processing</span>
              <span 
                className="text-sm font-mono font-semibold"
                style={{ color: stageInfo.glowColor }}
              >
                {Math.round(progress)}%
              </span>
            </div>
            
            {/* Progress track */}
            <div className="relative h-2 bg-gray-800 rounded-full overflow-hidden border border-gray-700/50">
              {/* Progress fill */}
              <div 
                className="absolute left-0 top-0 h-full transition-all duration-700 ease-out"
                style={{ 
                  width: `${Math.min(progress, 100)}%`,
                  background: `linear-gradient(90deg, ${stageInfo.glowColor}80, ${stageInfo.glowColor})`,
                  boxShadow: `inset 0 1px 0 rgba(255,255,255,0.2), 0 0 8px ${stageInfo.glowColor}40`,
                }}
              />
              
              {/* Progress shine effect */}
              <div 
                className="absolute top-0 h-full w-20 opacity-60"
                style={{
                  background: `linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent)`,
                  animation: 'progressShine 2s ease-in-out infinite',
                  left: `${Math.max(0, Math.min(progress - 10, 90))}%`,
                }}
              />
            </div>
            
            {/* Status indicator */}
            <div className="flex items-center justify-center mt-4">
              <div 
                className="w-2 h-2 rounded-full mr-2"
                style={{
                  backgroundColor: stageInfo.glowColor,
                  boxShadow: `0 0 6px ${stageInfo.glowColor}`,
                  animation: 'statusPulse 1.5s ease-in-out infinite',
                }}
              />
              <span className="text-xs text-gray-400 font-medium">
                AI Processing Active
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Custom CSS animations */}
      <style>{`
        @keyframes laserSweep {
          0% { 
            transform: translateY(-100vh);
            opacity: 0;
          }
          5% { 
            opacity: 0.8;
          }
          95% { 
            opacity: 0.8;
          }
          100% { 
            transform: translateY(100vh);
            opacity: 0;
          }
        }
        
        @keyframes progressShine {
          0% { 
            transform: translateX(-100%);
            opacity: 0;
          }
          50% { 
            opacity: 1;
          }
          100% { 
            transform: translateX(400%);
            opacity: 0;
          }
        }
        
        @keyframes statusPulse {
          0%, 100% { 
            opacity: 1;
            transform: scale(1);
          }
          50% { 
            opacity: 0.6;
            transform: scale(1.2);
          }
        }
      `}</style>
    </div>
  );
};