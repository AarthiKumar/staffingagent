import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { AlertCircle } from 'lucide-react';

interface ManualInputDialogProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: { name?: string; email?: string; phone?: string }) => void;
  missingFields: string[];
  filename: string;
}

export function ManualInputDialog({
  open,
  onClose,
  onSubmit,
  missingFields,
  filename,
}: ManualInputDialogProps) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const data: { name?: string; email?: string; phone?: string } = {};

    if (missingFields.includes('name') && name) {
      data.name = name;
    }
    if (missingFields.includes('email') && email) {
      data.email = email;
    }
    if (missingFields.includes('phone') && phone) {
      data.phone = phone;
    }

    onSubmit(data);
  };

  const isValid = () => {
    if (missingFields.includes('name') && !name) return false;
    if (missingFields.includes('email') && !email) return false;
    if (missingFields.includes('phone') && !phone) return false;
    return true;
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-orange-500" />
            Missing Required Information
          </DialogTitle>
          <DialogDescription>
            We couldn't extract all required information from <strong>{filename}</strong>.
            Please provide the missing details below.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit}>
          <div className="space-y-4 py-4">
            {missingFields.includes('name') && (
              <div className="space-y-2">
                <Label htmlFor="name" className="text-sm font-medium">
                  Name <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Enter candidate name"
                  required
                  className="w-full"
                />
              </div>
            )}

            {missingFields.includes('email') && (
              <div className="space-y-2">
                <Label htmlFor="email" className="text-sm font-medium">
                  Email <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="candidate@example.com"
                  required
                  className="w-full"
                />
              </div>
            )}

            {missingFields.includes('phone') && (
              <div className="space-y-2">
                <Label htmlFor="phone" className="text-sm font-medium">
                  Phone <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="phone"
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="(123) 456-7890"
                  required
                  className="w-full"
                />
              </div>
            )}

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-800">
              <strong>Tip:</strong> This information is required to create a candidate profile
              and enable duplicate detection.
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={!isValid()} className="bg-blue-600 hover:bg-blue-700">
              Submit and Continue
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
