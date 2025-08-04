import React from 'react';
import { clsx } from 'clsx';

interface LaserScanAnimationProps {
  isActive: boolean;
  className?: string;
  progress?: number; // 0-100
  stage?: 'preparing' | 'connecting' | 'masking' | 'inpainting' | 'finalizing' | 'starting' | 'processing';
  message?: string;
}

export const LaserScanAnimation: React.FC<LaserScanAnimationProps> = ({ 
  isActive, 
  className,
  progress = 0,
  stage = 'processing',
  message = 'Processing...'
}) => {
  if (!isActive) return null;

  const getStageInfo = () => {
    switch (stage) {
      case 'preparing':
      case 'connecting':
        return { 
          progressColor: 'from-blue-400 to-blue-600',
          glowColor: '#3b82f6',
          laserColor: '#dbeafe', // blue-100
          stageName: 'Preparing'
        };
      case 'masking':
        return { 
          progressColor: 'from-yellow-400 to-orange-500',
          glowColor: '#f59e0b',
          laserColor: '#fef3c7', // yellow-100
          stageName: 'Creating Masks'
        };
      case 'inpainting':
      case 'processing':
        return { 
          progressColor: 'from-green-400 to-green-600',
          glowColor: '#10b981',
          laserColor: '#dcfce7', // green-100
          stageName: 'AI Processing'
        };
      case 'finalizing':
        return { 
          progressColor: 'from-purple-400 to-purple-600',
          glowColor: '#8b5cf6',
          laserColor: '#ede9fe', // purple-100
          stageName: 'Finalizing'
        };
      default:
        return { 
          progressColor: 'from-blue-400 to-blue-600',
          glowColor: '#3b82f6',
          laserColor: '#dbeafe',
          stageName: 'Processing'
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
        <div className="mx-auto px-8 py-6 bg-gray-900/95 backdrop-blur-lg rounded-xl border border-gray-700/50 shadow-2xl">
          <div className="w-96">
            {/* Header with stage and progress */}
            <div className="flex justify-between items-center mb-4">
              <div className="flex items-center space-x-3">
                <div 
                  className="w-3 h-3 rounded-full"
                  style={{
                    backgroundColor: stageInfo.glowColor,
                    boxShadow: `0 0 8px ${stageInfo.glowColor}`,
                    animation: 'statusPulse 1.5s ease-in-out infinite',
                  }}
                />
                <span className="text-lg font-semibold text-white">
                  {stageInfo.stageName}
                </span>
              </div>
              <span 
                className="text-2xl font-mono font-bold"
                style={{ color: stageInfo.glowColor }}
              >
                {Math.round(progress)}%
              </span>
            </div>
            
            {/* Progress track */}
            <div className="relative h-3 bg-gray-800 rounded-full overflow-hidden border border-gray-700/50 mb-4">
              {/* Progress fill */}
              <div 
                className="absolute left-0 top-0 h-full transition-all duration-300 ease-out"
                style={{ 
                  width: `${Math.min(progress, 100)}%`,
                  background: `linear-gradient(90deg, ${stageInfo.glowColor}80, ${stageInfo.glowColor})`,
                  boxShadow: `inset 0 1px 0 rgba(255,255,255,0.2), 0 0 10px ${stageInfo.glowColor}40`,
                }}
              />
              
              {/* Progress shine effect */}
              <div 
                className="absolute top-0 h-full w-24 opacity-70"
                style={{
                  background: `linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent)`,
                  animation: 'progressShine 2s ease-in-out infinite',
                  left: `${Math.max(0, Math.min(progress - 12, 88))}%`,
                }}
              />
            </div>
            
            {/* Status message */}
            <div className="text-center mb-6">
              <p className="text-sm text-gray-300 font-medium">
                {message}
              </p>
            </div>

            {/* AI branding */}
            <div className="flex items-center justify-center pt-3 border-t border-gray-700/50">
              <span className="text-xs text-gray-500 font-medium">
                🤖 AI Processing Active
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