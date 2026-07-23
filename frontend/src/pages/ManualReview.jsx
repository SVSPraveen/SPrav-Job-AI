import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { ExternalLink, CheckCircle, FileText, BookOpen, X } from 'lucide-react';

export default function ManualReview() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedStrategy, setSelectedStrategy] = useState(null);
  const [userName, setUserName] = useState('User_Name');

  useEffect(() => {
    fetchJobs();
    fetchUserName();
  }, []);

  const fetchUserName = async () => {
    try {
      const res = await axios.get('http://127.0.0.1:8000/api/kb');
      const name = res.data?.personal?.name || 'User_Name';
      setUserName(name.replace(/ /g, '_'));
    } catch (e) { /* keep default */ }
  };

  const fetchJobs = async () => {
    try {
      const response = await axios.get('http://127.0.0.1:8000/api/jobs/manual');
      setJobs(response.data);
    } catch (error) {
      console.error("Failed to fetch manual jobs", error);
    } finally {
      setLoading(false);
    }
  };

  const markAsApplied = async (jobId) => {
    try {
      await axios.post(`http://127.0.0.1:8000/api/jobs/${jobId}/apply`);
      setJobs(jobs.filter(j => j.id !== jobId));
    } catch (error) {
      console.error("Failed to mark job as applied", error);
    }
  };

  const approveCoverLetter = async (jobId) => {
    try {
      await axios.post(`http://127.0.0.1:8000/api/jobs/${jobId}/approve-cover`);
      setJobs(jobs.map(j => j.id === jobId ? {...j, status: 'approved_for_dispatch'} : j));
      alert('Cover letter approved! The daemon will dispatch the application on the next cycle.');
    } catch (error) {
      console.error("Failed to approve cover letter", error);
    }
  };

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-400"></div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto p-8 animate-fade-in">
      <div className="mb-10">
        <h1 className="text-4xl font-bold text-white mb-3">Human Interaction Required</h1>
        <p className="text-gray-400 text-lg">
          The SPrav MoE Pipeline successfully generated ATS-optimized resumes for these roles, but could not automatically submit them (e.g. Workday portals). Apply manually and mark them as done.
        </p>
      </div>

      {jobs.length === 0 ? (
        <div className="bg-gray-800/50 rounded-2xl p-12 text-center border border-gray-700/50 backdrop-blur-sm">
          <CheckCircle className="mx-auto h-16 w-16 text-emerald-400 mb-4 opacity-80" />
          <h3 className="text-2xl font-medium text-white mb-2">You're all caught up!</h3>
          <p className="text-gray-400">The daemon will notify you when more secure portals require your intervention.</p>
        </div>
      ) : (
        <div className="grid gap-6">
          {jobs.map(job => (
            <div key={job.id} className="bg-gray-800/40 rounded-xl p-6 border border-gray-700/60 flex flex-col md:flex-row gap-6 hover:bg-gray-800/60 transition-colors">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="text-xl font-semibold text-white">{job.title}</h3>
                  {job.status === 'pending_cover_letter' ? (
                    <span className="px-3 py-1 bg-purple-500/10 text-purple-400 text-xs font-medium rounded-full border border-purple-500/20">
                      Awaiting Your Approval
                    </span>
                  ) : (
                    <span className="px-3 py-1 bg-amber-500/10 text-amber-400 text-xs font-medium rounded-full border border-amber-500/20">
                      Action Required
                    </span>
                  )}
                </div>
                <p className="text-gray-300 text-lg mb-4">{job.company}</p>
                
                <div className="flex flex-wrap items-center gap-3 text-sm">
                  <a 
                    href={job.url} 
                    target="_blank" 
                    rel="noreferrer"
                    className="flex items-center gap-2 bg-indigo-500 hover:bg-indigo-600 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                  >
                    <ExternalLink size={16} /> Open Link
                  </a>
                  <button 
                    onClick={() => {
                        const safeTitle = job.title.replace(/ /g, "_").replace(/\//g, "-");
                        const filename = `${userName}_${safeTitle}.pdf`;
                        alert(`Please retrieve ${filename} from your output folder.`);
                    }}
                    className="flex items-center gap-2 bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                  >
                    <FileText size={16} /> Locate PDF
                  </button>
                  {job.strategy_report && (
                    <button 
                      onClick={() => setSelectedStrategy(job.strategy_report)}
                      className="flex items-center gap-2 bg-fuchsia-600 hover:bg-fuchsia-500 text-white px-4 py-2 rounded-lg font-medium transition-colors border border-fuchsia-400/50"
                    >
                      <BookOpen size={16} /> View Strategy Report
                    </button>
                  )}
                </div>
              </div>

              <div className="flex flex-col gap-3 items-center border-t md:border-t-0 md:border-l border-gray-700 pt-6 md:pt-0 md:pl-6">
                {job.status === 'pending_cover_letter' ? (
                  <button 
                    onClick={() => approveCoverLetter(job.id)}
                    className="flex items-center justify-center gap-2 w-full md:w-auto bg-purple-500/20 hover:bg-purple-500/30 text-purple-300 border border-purple-500/40 px-6 py-3 rounded-xl font-semibold transition-all hover:scale-[1.02]"
                  >
                    <CheckCircle size={20} /> Approve &amp; Dispatch
                  </button>
                ) : (
                  <button 
                    onClick={() => markAsApplied(job.id)}
                    className="flex items-center justify-center gap-2 w-full md:w-auto bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-6 py-3 rounded-xl font-semibold transition-all hover:scale-[1.02]"
                  >
                    <CheckCircle size={20} /> Mark as Applied
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Strategy Report Modal */}
      {selectedStrategy && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in">
          <div className="bg-gray-900 border border-fuchsia-500/30 rounded-2xl w-full max-w-4xl max-h-[85vh] flex flex-col shadow-2xl shadow-fuchsia-900/20">
            <div className="flex items-center justify-between p-6 border-b border-gray-800">
              <h2 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-fuchsia-400 to-indigo-400 flex items-center gap-2">
                <BookOpen className="text-fuchsia-400" /> SPrav Strategy Report
              </h2>
              <button onClick={() => setSelectedStrategy(null)} className="text-gray-400 hover:text-white transition-colors bg-gray-800 hover:bg-gray-700 p-2 rounded-full">
                <X size={20} />
              </button>
            </div>
            <div className="p-8 overflow-y-auto custom-scrollbar">
              <pre className="text-gray-300 font-sans whitespace-pre-wrap leading-relaxed text-lg">
                {selectedStrategy}
              </pre>
            </div>
            <div className="p-6 border-t border-gray-800 bg-gray-900/50 flex justify-end rounded-b-2xl">
              <button 
                onClick={() => {
                  navigator.clipboard.writeText(selectedStrategy);
                  alert("Copied to clipboard!");
                }}
                className="bg-gray-800 hover:bg-gray-700 text-white px-6 py-2 rounded-lg font-medium transition-colors border border-gray-700"
              >
                Copy All Text
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
