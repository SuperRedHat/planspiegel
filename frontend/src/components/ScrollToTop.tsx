import { useEffect, useRef, useState } from "react";
import { ChevronUpIcon } from "@heroicons/react/24/outline";

export default function ScrollToTop({ children, height = "auto", maxHeight = "400px" }: {
  children: React.ReactNode;
  height?: string;
  maxHeight?: string;
}){
  const [isVisible, setIsVisible] = useState(false);
  const divRef = useRef<HTMLDivElement>(null);

  // Scroll to the top of the division
  const scrollToTop = () => {
    if (divRef.current) {
      divRef.current.scrollTo({
        top: 0,
        behavior: "smooth",
      });
    }
  };

  // Show "Scroll to Top" button based on scroll position
  const handleScroll = () => {
    if (divRef.current) {
      const scrollTop = divRef.current.scrollTop;
      setIsVisible(scrollTop > 100); // Show button if scrolled down by 100px
    }
  };

  useEffect(() => {
    const divElement = divRef.current;
    if (divElement) {
      divElement.addEventListener("scroll", handleScroll);
      // Scroll to bottom on mount
      setTimeout(() => {
        divElement.scrollTo({
          top: divElement.scrollHeight,
          behavior: "smooth",
        });
      }, 100);
      return () => divElement.removeEventListener("scroll", handleScroll);
    }
  }, []);

  return (
    <div style={{ position: "relative" }}>
      {/* Scrollable Div */}
      <div
        ref={divRef}
        style={{
          height,
          maxHeight,
          overflowY: "auto",
          padding: "10px",
        }}
      >
        {children}

      </div>

      {/* Scroll to Top Button */}
      {isVisible && (

        <button
          onClick={scrollToTop}
          className="scroll-to-top-button"
        >
          <ChevronUpIcon className="size-4 font-medium" />
        </button>
      )}
    </div>
  );
};