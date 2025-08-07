import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { CheckCircle } from 'lucide-react';

interface WelcomeModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const WelcomeModal = ({ isOpen, onClose }: WelcomeModalProps) => {
  const handleComplete = () => {
    localStorage.setItem('onboarding_completed', 'true');
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <CheckCircle className="h-5 w-5 text-green-500" />
            Welcome to Synapse AI!
          </DialogTitle>
          <DialogDescription>
            Let's get you started with the key features of your new AI workspace.
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <h4 className="font-medium text-sm">🎛️ Power Level Selector</h4>
            <p className="text-sm text-muted-foreground">
              Choose the right AI model for your task - from quick responses to deep analysis.
            </p>
          </div>
          
          <div className="space-y-2">
            <h4 className="font-medium text-sm">💳 Credit System</h4>
            <p className="text-sm text-muted-foreground">
              Monitor your usage and upgrade your plan as needed. Different models consume different amounts of credits.
            </p>
          </div>
          
          <div className="space-y-2">
            <h4 className="font-medium text-sm">📑 Tabbed Output</h4>
            <p className="text-sm text-muted-foreground">
              View and compare results from different AI models in organized tabs for easy analysis.
            </p>
          </div>
        </div>
        
        <div className="flex justify-end">
          <Button onClick={handleComplete}>
            Got it, let's start!
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default WelcomeModal;
