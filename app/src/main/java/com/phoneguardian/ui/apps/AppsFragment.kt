package com.phoneguardian.ui.apps

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.phoneguardian.R
import com.phoneguardian.databinding.FragmentAppsBinding
import com.phoneguardian.util.TimeUtils
import kotlinx.coroutines.launch

class AppsFragment : Fragment() {

    private var _binding: FragmentAppsBinding? = null
    private val binding get() = _binding!!

    private val viewModel: AppsViewModel by viewModels()
    private val appAdapter = AppListAdapter()
    private val chargeCycleAdapter = ChargeCycleAdapter()

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
            adapter = chargeCycleAdapter
        }
    }

    private fun observeUiState() {
        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.uiState.collect { state ->
                    appAdapter.submitList(state.topApps)
                    binding.tvNoApps.visibility = if (state.topApps.isEmpty()) View.VISIBLE else View.GONE

                    chargeCycleAdapter.submitList(state.recentChargeCycles)
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
    private var maxDuration: Long = 1

    fun submitList(newItems: List<AppInfo>) {
        items = newItems
        maxDuration = newItems.maxOfOrNull { it.duration }?.coerceAtLeast(1) ?: 1
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_app_usage, parent, false)
        return ViewHolder(view)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val app = items[position]
        holder.bind(app, position + 1, maxDuration)
    }

    override fun getItemCount() = items.size

    class ViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        fun bind(app: AppInfo, rank: Int, maxDuration: Long) {
            itemView.findViewById<TextView>(R.id.tvRank).text = rank.toString()
            itemView.findViewById<TextView>(R.id.tvAppName).text = app.name
            itemView.findViewById<TextView>(R.id.tvDuration).text = TimeUtils.formatDuration(app.duration)

            val progressView = itemView.findViewById<View>(R.id.vProgressBar)
            val trackView = itemView.findViewById<View>(R.id.vProgressTrack)
            val ratio = (app.duration.toFloat() / maxDuration).coerceIn(0f, 1f)
            val lp = progressView.layoutParams as android.widget.LinearLayout.LayoutParams
            lp.weight = ratio
            progressView.layoutParams = lp
            val tp = trackView.layoutParams as android.widget.LinearLayout.LayoutParams
            tp.weight = 1f - ratio
            trackView.layoutParams = tp
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
            .inflate(R.layout.item_charge_cycle, parent, false)
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
            itemView.findViewById<TextView>(R.id.tvCycleInfo).text =
                "${cycle.date}  |  $levelInfo"
            itemView.findViewById<TextView>(R.id.tvCycleDetail).text =
                "充电时长: ${cycle.duration}  |  期间亮屏: ${cycle.screenTimeDuringCharge}"
        }
    }
}
