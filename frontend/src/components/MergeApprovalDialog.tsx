import { useState } from 'react';
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
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, ArrowRight, CheckCircle } from 'lucide-react';

interface MergeProposal {
  duplicate_found: boolean;
  existing_candidate_id: string;
  existing_data: {
    name: string;
    email: string | null;
    phone: string | null;
    location: string | null;
  };
  new_data: {
    name: string;
    email: string | null;
    phone: string | null;
    location: string | null;
  };
  suggested_merge: {
    name: string;
    email: string | null;
    phone: string | null;
    location: string | null;
  };
  conflict_fields: string[];
}

interface MergeApprovalDialogProps {
  open: boolean;
  onClose: () => void;
  onApprove: (mergedData: any) => void;
  mergeProposal: MergeProposal;
  filename: string;
  isSubmitting?: boolean;
}

export function MergeApprovalDialog({
  open,
  onClose,
  onApprove,
  mergeProposal,
  filename,
  isSubmitting = false,
}: MergeApprovalDialogProps) {
  const [editedData, setEditedData] = useState(mergeProposal.suggested_merge);

  const handleFieldChange = (field: string, value: string) => {
    setEditedData((prev) => ({ ...prev, [field]: value }));
  };

  const handleApprove = () => {
    onApprove(editedData);
  };

  const isConflict = (field: string) => {
    return mergeProposal.conflict_fields.includes(field);
  };

  const ComparisonRow = ({
    label,
    field,
    existing,
    newValue,
  }: {
    label: string;
    field: string;
    existing: string | null;
    newValue: string | null;
  }) => {
    const hasConflict = isConflict(field);

    return (
      <div className="space-y-2">
        <Label className="text-sm font-medium flex items-center gap-2">
          {label}
          {hasConflict && (
            <Badge variant="warning" className="text-xs">
              Conflict
            </Badge>
          )}
        </Label>

        <div className="grid grid-cols-3 gap-3 items-center">
          {/* Existing */}
          <div
            className={`p-3 rounded-lg border text-sm ${
              hasConflict ? 'bg-orange-50 border-orange-200' : 'bg-gray-50 border-gray-200'
            }`}
          >
            <div className="text-xs text-gray-500 mb-1">Current</div>
            <div className="font-medium">{existing || <span className="text-gray-400">Not set</span>}</div>
          </div>

          {/* Arrow */}
          <div className="flex justify-center">
            <ArrowRight className="h-4 w-4 text-gray-400" />
          </div>

          {/* New */}
          <div
            className={`p-3 rounded-lg border text-sm ${
              hasConflict ? 'bg-blue-50 border-blue-200' : 'bg-gray-50 border-gray-200'
            }`}
          >
            <div className="text-xs text-gray-500 mb-1">New CV</div>
            <div className="font-medium">{newValue || <span className="text-gray-400">Not set</span>}</div>
          </div>
        </div>

        {/* Editable merged value */}
        <div className="pt-2">
          <div className="text-xs text-gray-500 mb-1">Merged Value (editable):</div>
          <Input
            value={editedData[field as keyof typeof editedData] || ''}
            onChange={(e) => handleFieldChange(field, e.target.value)}
            placeholder={`Enter ${label.toLowerCase()}`}
            className="w-full"
          />
        </div>
      </div>
    );
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[700px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-orange-500" />
            Duplicate Candidate Detected
          </DialogTitle>
          <DialogDescription>
            A candidate with matching information already exists. The new CV from{' '}
            <strong>{filename}</strong> will be linked to the existing candidate.
            Review and approve the merged data below.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Info Banner */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <CheckCircle className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-blue-900">
                <p className="font-medium mb-1">Both CVs will be kept</p>
                <p className="text-blue-700">
                  The existing CV and the new CV will both be linked to this candidate,
                  allowing you to access both documents and their full history.
                </p>
              </div>
            </div>
          </div>

          {/* Field Comparisons */}
          <div className="space-y-6">
            <ComparisonRow
              label="Name"
              field="name"
              existing={mergeProposal.existing_data.name}
              newValue={mergeProposal.new_data.name}
            />

            <ComparisonRow
              label="Email"
              field="email"
              existing={mergeProposal.existing_data.email}
              newValue={mergeProposal.new_data.email}
            />

            <ComparisonRow
              label="Phone"
              field="phone"
              existing={mergeProposal.existing_data.phone}
              newValue={mergeProposal.new_data.phone}
            />

            <ComparisonRow
              label="Location"
              field="location"
              existing={mergeProposal.existing_data.location}
              newValue={mergeProposal.new_data.location}
            />
          </div>

          {/* Conflict Summary */}
          {mergeProposal.conflict_fields.length > 0 && (
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
              <div className="text-sm text-orange-900">
                <p className="font-medium mb-1">⚠️ Conflicts detected in:</p>
                <ul className="list-disc list-inside space-y-1 text-orange-700">
                  {mergeProposal.conflict_fields.map((field) => (
                    <li key={field} className="capitalize">
                      {field}
                    </li>
                  ))}
                </ul>
                <p className="mt-2 text-orange-700">
                  Please review the merged values above and edit if needed.
                </p>
              </div>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={onClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button
            type="button"
            onClick={handleApprove}
            disabled={isSubmitting}
            className="bg-green-600 hover:bg-green-700"
          >
            {isSubmitting ? 'Approving...' : 'Approve Merge'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
