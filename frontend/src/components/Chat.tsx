import API from "@app/api/api";
import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkRehype from "remark-rehype";
import FileInput from "./FileInput";
import FilePreview from "./FilePreview";
import ScrollToTop from "./ScrollToTop";
interface Message {
  message_id: number;
  sender_type: "assistant" | "user" | "system";
  content: string;
}

interface File {
  name: string;
  blob: Blob;
  type: string;
  url: string;
}

export const Chat = ({
  chat_id,
  checkup_id,
  check_id,
}: {
  chat_id: string | undefined;
  checkup_id: string | undefined;
  check_id: string | undefined;
}) => {
  const [selectedPreview, setSelectedPreview] = useState<File>();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messageIdCounter = useRef(1);

  useEffect(() => {
    if (checkup_id && check_id && chat_id) {
      API.chat.getMessageHistory(checkup_id, check_id, chat_id).then((res) => {
        messageIdCounter.current = res.data[0]?.message_id + 1 || 1;
        setMessages(res.data?.reverse());
      });
    }
  }, [checkup_id, check_id, chat_id]);

  const onFilesInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const filesArr = e.target.files;
    if (filesArr) {
      const file = filesArr[0];
      setSelectedPreview({
        name: file.name,
        url: URL.createObjectURL(file),
        type: file.type,
        blob: file,
      });
    }
  };
  const sendMessage = async (question: string) => {
    if (!question.trim()) return;

    // Add user message
    const userMessageId = messageIdCounter.current++;
    setMessages((prev) => [
      ...prev,
      {
        message_id: userMessageId,
        sender_type: "user",
        content: question,
      },
    ]);

    setIsLoading(true);

    const formData = new FormData();
    formData.append("question", question);
    formData.append("use_stream", "true");
    if (selectedPreview) {
      formData.append("file", selectedPreview.blob);
    }

    try {
      const response = await fetch(
        `${
          import.meta.env.VITE_API_URL
        }/checkups/${checkup_id}/checks/${check_id}/chats/${chat_id}/messages`,
        {
          method: "POST",
          headers: {
            "Cache-Control": "no-cache",
          },
          body: formData,
          credentials: "include",
        }
      );

      if (response.status !== 200 && response.status !== 201) {
        throw new Error(
          `Network error: ${response.status} - ${response.statusText}`
        );
      }

      const stream = response.body!.pipeThrough(new TextDecoderStream());
      const reader = stream.getReader();
      let botMessage = "";
      const botMessageId = messageIdCounter.current++;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        botMessage += value;
        // Update the bot message in real-time
        setMessages((prev) => {
          const existing = prev.find((m) => m.message_id === botMessageId);
          if (existing) {
            return prev.map((m) =>
              m.message_id === botMessageId ? { ...m, content: botMessage } : m
            );
          } else {
            return [
              ...prev,
              {
                message_id: botMessageId,
                sender_type: "assistant",
                content: botMessage,
              },
            ];
          }
        });
      }
    } catch (error) {
      console.error("Error:", error);

      // 忽略 200 状态的异常
      if (
        error instanceof TypeError &&
        error.message.includes("network error")
      ) {
        console.warn("Ignoring harmless network error:", error);
        return;
      }

      setMessages((prev) => [
        ...prev,
        {
          message_id: messageIdCounter.current++,
          sender_type: "system",
          content: "Error: Could not send message",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputMessage.trim() && !isLoading) {
      sendMessage(inputMessage);
      setInputMessage("");
      setSelectedPreview(undefined);
    }
  };

  return (
    <div className="border-t border-gray-200 py-5 sm:px-2 print:hidden">
      <dl className="grid grid-cols-1 gap-x-4 gap-y-8 sm:grid-cols-4 divide-x divide-gray-200">
        <div className="sm:col-span-4">
          <dt className="text-sm font-medium text-gray-500">Chat</dt>
          <dd className="mt-1 text-sm text-gray-900 px-4">
            {messages.length > 0 && (
              <ScrollToTop maxHeight={"400px"}>
                <div className="flex-1 space-y-4 p-4 pb-0 bg-gray-50 rounded-lg">
                  {messages.map((message) => (
                    <div
                      key={message.message_id}
                      className={`flex ${
                        message.sender_type === "assistant"
                          ? "justify-start"
                          : message.sender_type === "system"
                          ? "justify-center"
                          : "justify-end"
                      }`}
                    >
                      <div
                        className={`rounded-lg px-4 py-2 max-w-[80%] ${
                          message.sender_type === "assistant"
                            ? "bg-slate-100 shadow-sm"
                            : message.sender_type === "system"
                            ? "bg-gray-100 text-gray-600 text-center"
                            : "bg-sky-100 text-sky-900"
                        }`}
                      >
                        <ReactMarkdown
                          remarkPlugins={[[remarkGfm], [remarkRehype]]}
                          className="prose prose-sm max-w-none"
                        >
                          {message.content}
                        </ReactMarkdown>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollToTop>
            )}
            <div className="border-t border-gray-200 pt-4">
              {selectedPreview && (
                <FilePreview
                  value={selectedPreview}
                  onDelete={() => setSelectedPreview(undefined)}
                />
              )}
              <form onSubmit={handleSubmit}>
                <div className="flex flex-row space-x-2">
                  <FileInput chat_id={chat_id} onInput={onFilesInput} />
                  <input
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    placeholder="Type your message..."
                    className="flex-1 rounded-md px-3 focus:ring-sky-100 focus:ring-1 focus:outline-none"
                    disabled={isLoading}
                  />
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="inline-flex items-center rounded-md border bg-transparent text-sky-500 border-sky-500 px-3 py-2 text-sm font-semibold shadow-sm hover:bg-sky-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-500"
                  >
                    {isLoading ? "Sending..." : "Send"}
                  </button>
                </div>
              </form>
            </div>
          </dd>
        </div>
      </dl>
    </div>
  );
};
