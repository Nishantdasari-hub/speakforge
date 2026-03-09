import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Swal from "sweetalert2";

export default function AdminTests() {

  const [tests, setTests] = useState([]);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [editingId, setEditingId] = useState(null);
  const [editTitle, setEditTitle] = useState("");
  const [editDescription, setEditDescription] = useState("");

  const token = localStorage.getItem("token");

  const loadTests = async () => {
    const res = await fetch("http://127.0.0.1:8000/tests/", {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    const data = await res.json();
    setTests(data);
  };

useEffect(() => {
    loadTests();
  }, []);

  const createTest = async () => {
    if (!title) {
      Swal.fire("Error", "Title is required", "error");
      return;
    }

    await fetch("http://127.0.0.1:8000/tests/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify({
        title,
        description
      })
    });

    setTitle("");
    setDescription("");

    loadTests();

    Swal.fire("Success", "Test created successfully", "success");
  };

  const deleteTest = async (id) => {
    const confirm = await Swal.fire({
      title: "Delete Test?",
      icon: "warning",
      showCancelButton: true
    });

    if (!confirm.isConfirmed) return;

    try {
      const response = await fetch(`http://127.0.0.1:8000/tests/${id}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      if (response.ok) {
        loadTests();
        Swal.fire("Success", "Test deleted successfully", "success");
      } else {
        Swal.fire("Error", "Failed to delete test", "error");
      }
    } catch (error) {
      Swal.fire("Error", "Network error", "error");
    }
  };

  // Start Edit Test
  const startEditTest = (test) => {
    setEditingId(test.id);
    setEditTitle(test.title);
    setEditDescription(test.description);
  };

  // Save Edited Test
  const saveEditTest = async () => {
    if (!editingId) return;

    try {
      const response = await fetch(`http://127.0.0.1:8000/tests/${editingId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          title: editTitle,
          description: editDescription
        })
      });

      if (response.ok) {
        await loadTests();
        setEditingId(null);
        Swal.fire("Success", "Test updated successfully", "success");
      } else {
        Swal.fire("Error", "Failed to update test", "error");
      }
    } catch (error) {
      Swal.fire("Error", "Network error", "error");
    }
  };

  // Cancel Edit
  const cancelEdit = () => {
    setEditingId(null);
    setEditTitle("");
    setEditDescription("");
  };

  return (
    <div className="text-white">
      <h1 className="text-3xl font-bold mb-8">
        Manage Tests
      </h1>

      {/* Edit Test Form */}
      {editingId && (
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white/10 backdrop-blur-lg p-8 rounded-xl w-[500px] mb-12 border-2 border-yellow-500"
        >
          <h2 className="text-xl mb-4 text-yellow-400">
            Edit Test
          </h2>

          <input
            value={editTitle}
            onChange={(e) => setEditTitle(e.target.value)}
            placeholder="Test Title"
            className="w-full p-3 mb-4 bg-black/40 border border-gray-600 rounded"
          />

          <textarea
            value={editDescription}
            onChange={(e) => setEditDescription(e.target.value)}
            placeholder="Test Description"
            className="w-full p-3 mb-4 bg-black/40 border border-gray-600 rounded"
          />

          <div className="flex gap-2">
            <button
              onClick={saveEditTest}
              className="bg-green-600 px-6 py-2 rounded hover:bg-green-700"
            >
              Save Changes
            </button>
            <button
              onClick={cancelEdit}
              className="bg-gray-500 px-6 py-2 rounded hover:bg-gray-600"
            >
              Cancel
            </button>
          </div>
        </motion.div>
      )}

      {/* Create Test Card */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white/10 backdrop-blur-lg p-8 rounded-xl w-[500px] mb-12"
      >
        <h2 className="text-xl mb-4">
          Create New Test
        </h2>

        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Test Title"
          className="w-full p-3 mb-4 bg-black/40 border border-gray-600 rounded"
        />

        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Test Description"
          className="w-full p-3 mb-4 bg-black/40 border border-gray-600 rounded"
        />

        <button
          onClick={createTest}
          className="bg-blue-600 px-6 py-2 rounded hover:bg-blue-700"
        >
          Create Test
        </button>
      </motion.div>

      {/* Tests List */}
      <h2 className="text-xl mb-6">
        Existing Tests
      </h2>

      <div className="grid gap-4">
        {tests.map((test, index) => (
          <motion.div
            key={test.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-white/10 backdrop-blur-lg border border-white/20 p-6 rounded-xl flex justify-between items-center"
          >
            <div>
              <h3 className="text-lg font-semibold">
                {test.title}
              </h3>
              <p className="text-gray-400 text-sm">
                {test.description}
              </p>
            </div>

            <div className="flex gap-3">
              {editingId === test.id ? (
                <div className="flex gap-2">
                  <button
                    onClick={saveEditTest}
                    className="bg-green-500 px-3 py-1 rounded hover:bg-green-600 text-sm"
                  >
                    Save
                  </button>
                  <button
                    onClick={cancelEdit}
                    className="bg-gray-500 px-3 py-1 rounded hover:bg-gray-600 text-sm"
                  >
                    Cancel
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => startEditTest(test)}
                  className="bg-yellow-500 px-4 py-2 rounded hover:bg-yellow-600"
                >
                  Edit
                </button>
              )}

              <button
                onClick={() => deleteTest(test.id)}
                className="bg-red-500 px-4 py-2 rounded hover:bg-red-600"
              >
                Delete
              </button>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );

}
