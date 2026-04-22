package com.phoneguardian.ui.apps

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.phoneguardian.databinding.FragmentAppsBinding
import com.phoneguardian.util.TimeUtils
import kotlinx.coroutines.launch

class AppsFragment : Fragment() {

    private var _binding: FragmentAppsBinding? = null
    private val binding get() = _binding!!

    private val viewModel: AppsViewModel by viewModels()
    private val appAdapter = AppListAdapter()

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentAppsBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        setupRecyclerView()
        observeUiState()
    }

    private fun setupRecyclerView() {
        binding.rvApps.apply {
            layoutManager = LinearLayoutManager(requireContext())
            adapter = appAdapter
        }

        binding.rvChargeCycles.apply {
            layoutManager = LinearLayoutManager(requireContext())
            adapter = ChargeCycleAdapter()
        }
    }

    private fun observeUiState() {
        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.uiState.collect { state ->
                    appAdapter.submitList(state.topApps)
                    binding.tvNoApps.visibility = if (state.topApps.isEmpty()) View.VISIBLE else View.GONE

                    binding.tvChargeCyclesTitle.text = "最近充电周期 (${state.recentChargeCycles.size})"
                }
            }
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}

class AppListAdapter : RecyclerView.Adapter<AppListAdapter.ViewHolder>() {

    private var items: List<AppInfo> = emptyList()

    fun submitList(newItems: List<AppInfo>) {
        items = newItems
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(android.R.layout.simple_list_item_2, parent, false)
        return ViewHolder(view)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val app = items[position]
        holder.bind(app, position + 1)
    }

    override fun getItemCount() = items.size

    class ViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        fun bind(app: AppInfo, rank: Int) {
            itemView.findViewById<android.widget.TextView>(android.R.id.text1).text =
                "$rank. ${app.name}"
            itemView.findViewById<android.widget.TextView>(android.R.id.text2).text =
                TimeUtils.formatDuration(app.duration)
        }
    }
}

class ChargeCycleAdapter : RecyclerView.Adapter<ChargeCycleAdapter.ViewHolder>() {

    private var items: List<ChargeCycleInfo> = emptyList()

    fun submitList(newItems: List<ChargeCycleInfo>) {
        items = newItems
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(android.R.layout.simple_list_item_2, parent, false)
        return ViewHolder(view)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        holder.bind(items[position])
    }

    override fun getItemCount() = items.size

    class ViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        fun bind(cycle: ChargeCycleInfo) {
            val levelInfo = if (cycle.endLevel != null) {
                "${cycle.startLevel}% → ${cycle.endLevel}%"
            } else {
                "${cycle.startLevel}% → ?%"
            }
            itemView.findViewById<android.widget.TextView>(android.R.id.text1).text =
                "${cycle.date} | $levelInfo"
            itemView.findViewById<android.widget.TextView>(android.R.id.text2).text =
                "充电时长: ${cycle.duration} | 期间亮屏: ${cycle.screenTimeDuringCharge}"
        }
    }
}
