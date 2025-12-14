/* eslint-disable @typescript-eslint/no-explicit-any */
import { FaPaperclip } from "react-icons/fa";

const FileInput = ({
  chat_id,
  onInput,
}: {
  chat_id: string | undefined;
  onInput: (e: any) => void;
}) => {
  const resetFiles = (e: any) => {
    e.target.value = null;
  };
  return (
    <>
      <input
        type="file"
        multiple={false}
        id={`chatbot-select_file_${chat_id}`}
        style={{ display: "none" }}
        accept="image/png,image/jpeg,image/jpg"
        onClick={resetFiles}
        onInput={(e) => onInput(e)}
      />
      <button
        type="button"
        className="font-medium text-white text-xs cursor-pointer hover:text-white bg-sky-500 outline-none px-2 py-1 rounded-md hover:bg-sky-600"
        onClick={() => document.getElementById(`chatbot-select_file_${chat_id}`)?.click()}
      >
        <div className="w-10 h-10 flex items-center justify-center">
          <FaPaperclip />
        </div>
      </button>{" "}
    </>
  );
};

export default FileInput;
