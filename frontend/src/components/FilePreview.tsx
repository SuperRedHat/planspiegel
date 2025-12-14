/* eslint-disable @typescript-eslint/no-explicit-any */
import { FaTimes } from "react-icons/fa";

interface FilePreview {
  name: string;
  blob: Blob;
  type: string;
  url: string;
}

const FilePreview = ({
  value,
  onDelete,
}: {
  value: FilePreview;
  onDelete: any;
}) => {
  if (value) {
    return (
      <div className="flex flex-row items-center w-full mb-2 h-[60px] p-[10px]">
        {value.url && value.type.includes("image/") && (
          <div className="group relative">
            <div className="relative h-[60px]">
              <img
                src={value.url}
                alt={value.name}
                className="w-[60px] min-w-[80px] h-full object-cover bg-gray-200 rounded-md overflow-hidden"
              />
              <button
                className="min-w-[16px] max-w-[16px] w-[16px] h-[16px] p-0 flex items-center justify-center text-white bg-black/50 hover:bg-black/70 text-[10px] absolute top-0 right-0"
                onClick={onDelete}
              >
                <FaTimes />
              </button>
            </div>
          </div>
        )}
        <p className="pl-4">{value.name}</p>
      </div>
    );
  } else {
    return null;
  }
};

export default FilePreview;
