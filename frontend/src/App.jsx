import React, { useState, useEffect } from "react";
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";

const App = () => {
  const [news, setNews] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  // Track expanded/collapsed cards
  const [expandedArticles, setExpandedArticles] = useState({});

  // Toggle Read More / Read Less
  const toggleArticle = (index) => {
    setExpandedArticles((prev) => ({
      ...prev,
      [index]: !prev[index],
    }));
  };

  useEffect(() => {
    const fetchNews = async () => {
      try {
        setLoading(true);
        setError(null);

        const url = import.meta.env.VITE_BACKEND_URL;

        const response = await fetch(`http://${url}/news`);

        if (!response.ok) {
          throw new Error("Failed to fetch news");
        }

        const data = await response.json();

        console.log("API RESPONSE:", data);

        // Use the fields directly from MongoDB/API
        const formattedNews = data.news.map((item) => {
          console.log("TITLE:", item.title);
          console.log("CONTENT:", item.content);
          console.log("CATEGORY:", item.category);
          console.log("IMAGE:", item.image_urls);

          return {
            title: item.title || "No title available",
            content: item.content || "",
            category: item.category || "General",
            image_urls: item.image_urls || "",
          };
        });

        // Get unique categories
        const uniqueCategories = [
          "All",
          ...new Set(formattedNews.map((item) => item.category)),
        ];

        setNews(formattedNews);
        setCategories(uniqueCategories);
      } catch (err) {
        console.error("FETCH NEWS ERROR:", err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    // Initial fetch
    fetchNews();

    // Refresh news periodically
    const interval = setInterval(fetchNews, 500000);

    return () => clearInterval(interval);
  }, []);

  // Filter news by selected category
  const filteredNews =
    selectedCategory === "All"
      ? news
      : news.filter((item) => item.category === selectedCategory);

  return (
    <div className="min-h-screen bg-gray-50">

      {/* Navbar */}
      <Navbar
        categories={categories}
        selectedCategory={selectedCategory}
        onCategoryChange={setSelectedCategory}
      />

      <main className="container mx-auto px-4 py-8">

        {/* Error Message */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* Loading */}
        {loading ? (
          <div className="flex justify-center items-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          <>
            {/* Page Title */}
            <h1 className="text-3xl font-bold text-gray-800 mb-8">
              {selectedCategory === "All"
                ? "Latest News"
                : `${selectedCategory} News`}
            </h1>

            {/* NEWS GRID */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

              {filteredNews.map((item, index) => {
                const isExpanded = expandedArticles[index];

                return (
                  <article
                    key={index}
                    className="bg-white rounded-lg shadow-md overflow-hidden flex flex-col hover:shadow-lg transition-shadow duration-300"
                  >

                    {/* IMAGE */}
                    {item.image_urls && (
                      <img
                        src={item.image_urls}
                        alt={item.title}
                        className="w-full h-75 object-cover"
                      />
                    )}

                    {/* CARD CONTENT */}
                    <div className="p-5 flex flex-col flex-1">

                      {/* TITLE */}
                      <h2 className="text-xl font-bold text-gray-800 mb-3">
                        {item.title}
                      </h2>

                      {/* CATEGORY */}
                      <div className="mb-4">
                        <span className="inline-block px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                          {item.category}
                        </span>
                      </div>

                      {/* ARTICLE CONTENT */}
                      <div
                        className={`text-gray-600 leading-relaxed whitespace-pre-line overflow-hidden transition-all duration-300 ${
                          isExpanded
                            ? "max-h-[1500px]"
                            : "max-h-32"
                        }`}
                      >
                        {item.content}
                      </div>

                      {/* READ MORE / READ LESS */}
                      <button
                        onClick={() => toggleArticle(index)}
                        className="mt-4 text-blue-600 hover:text-blue-800 font-medium text-left"
                      >
                        {isExpanded ? "Read less" : "Read more"}
                      </button>

                    </div>
                  </article>
                );
              })}

            </div>

            {/* No News */}
            {filteredNews.length === 0 && (
              <div className="text-center py-20 text-gray-500">
                No news available for this category.
              </div>
            )}
          </>
        )}

      </main>

      {/* Footer */}
      <Footer />

    </div>
  );
};

export default App;