import { useState } from 'react';
import axios from 'axios';

export function StemOptions() {
  const [selectedStems, setSelectedStems] = useState('4stems');
  
  const stemOptions = [
    { value: '2stems', label: '2 Stems', description: 'Vocals + Accompaniment' },
    { value: '4stems', label: '4 Stems', description: 'Vocals, Drums, Bass, Other' },
    { value: '6stems', label: '6 Stems', description: 'Vocals, Drums, Bass, Piano, Guitar, Other' },
  ];

  const separateAudio = async (audioFile: File) => {
    const formData = new FormData();
    formData.append('audio', audioFile);
    formData.append('stems', selectedStems);
    
    try {
      const res = await axios.post('/api/separate', formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      console.log("Backend response:", res.data);
      alert(`Separation successful: ${JSON.stringify(res.data)}`);
    } catch (error) {
      console.error("Error:", error);
      alert("Separation failed. Please try again.");
    }
  };

  return (
    <div className="mb-6">
      <h3 className="text-lg font-semibold mb-3">Select Stem Separation:</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {stemOptions.map((option) => (
          <div
            key={option.value}
            className={`border rounded-lg p-4 cursor-pointer transition-all ${
              selectedStems === option.value
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
            onClick={() => setSelectedStems(option.value)}
          >
            <div className="flex items-start">
              <div className={`w-5 h-5 rounded-full border mr-3 mt-1 ${
                selectedStems === option.value
                  ? 'border-blue-500 bg-blue-500'
                  : 'border-gray-300'
              }`} />
              <div>
                <h4 className="font-bold">{option.label}</h4>
                <p className="text-sm text-gray-600 mt-1">{option.description}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}