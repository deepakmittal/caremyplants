import React, { useRef } from 'react';
import { motion } from 'framer-motion';
import { ChevronLeft, ChevronRight } from 'lucide-react';

const Carousel = ({ children }) => {
    const scrollRef = useRef(null);

    const scroll = (direction) => {
        if (scrollRef.current) {
            const { scrollLeft, clientWidth } = scrollRef.current;
            const scrollTo = direction === 'left' ? scrollLeft - clientWidth : scrollLeft + clientWidth;
            scrollRef.current.scrollTo({ left: scrollTo, behavior: 'smooth' });
        }
    };

    return (
        <div className="relative group">
            <div
                ref={scrollRef}
                className="carousel-container"
            >
                {React.Children.map(children, (child) => (
                    <div className="carousel-item">
                        {child}
                    </div>
                ))}
            </div>

            <button
                onClick={() => scroll('left')}
                className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-4 bg-white/10 hover:bg-white/20 backdrop-blur-md p-3 rounded-full opacity-0 group-hover:opacity-100 transition-opacity border border-white/10 z-10 hidden md:block"
            >
                <ChevronLeft size={24} />
            </button>

            <button
                onClick={() => scroll('right')}
                className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-4 bg-white/10 hover:bg-white/20 backdrop-blur-md p-3 rounded-full opacity-0 group-hover:opacity-100 transition-opacity border border-white/10 z-10 hidden md:block"
            >
                <ChevronRight size={24} />
            </button>
        </div>
    );
};

export default Carousel;
