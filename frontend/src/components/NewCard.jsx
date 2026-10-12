import React, { useState } from "react";
import { ChevronUp } from "lucide-react";

const NewsCard = ({ item }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  console.log("NEWS ITEM:", item);
  console.log("TITLE:", item?.title);
  console.log("CONTENT:", item?.content);

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden transition-all duration-300 hover:shadow-xl mb-6">

      {/* Image */}
      {item?.image_urls && (
        <img
          src={item.image_urls}
          alt={item?.title || "News"}
          className="w-full h-48 object-cover rounded-t-lg"
        />
      )}

      <div className="p-6">

        {/* TITLE */}
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          {item?.title || "No title available"}
        </h2>

        {/* CATEGORY */}
        {item?.category && (
          <span className="inline-block px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm mb-4">
            {item.category}
          </span>
        )}

        {/* CONTENT */}
        <div
          className={`overflow-hidden transition-all duration-300 ${
            isExpanded ? "max-h-[3000px]" : "max-h-32"
          }`}
        >
          <div className="text-gray-700 leading-relaxed whitespace-pre-line">
            {item?.content || "No content available"}
          </div>
        </div>

        {/* READ MORE */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="mt-4 flex items-center text-blue-600 hover:text-blue-800"
        >
          {isExpanded ? "Read less" : "Read more"}

          <ChevronUp
            className={`ml-1 h-4 w-4 transition-transform duration-200 ${
              isExpanded ? "rotate-180" : ""
            }`}
          />
        </button>

      </div>
    </div>
  );
};

export default NewsCard;