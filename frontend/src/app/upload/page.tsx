import UploadDropzone from "@/components/upload-dropzone";

export default function UploadPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Upload Call</h1>
        <p className="text-gray-500 mt-1">Upload a sales call recording for automated QA evaluation</p>
      </div>
      <UploadDropzone />
    </div>
  );
}
