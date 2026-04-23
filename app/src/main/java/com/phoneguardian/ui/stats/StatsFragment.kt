package com.phoneguardian.ui.stats

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import com.google.android.material.tabs.TabLayout
import com.github.mikephil.charting.components.XAxis
import com.github.mikephil.charting.data.BarData
import com.github.mikephil.charting.data.BarDataSet
import com.github.mikephil.charting.data.BarEntry
import com.github.mikephil.charting.formatter.IndexAxisValueFormatter
import com.phoneguardian.R
import com.phoneguardian.databinding.FragmentStatsBinding
import com.phoneguardian.util.TimeUtils
import kotlinx.coroutines.launch

class StatsFragment : Fragment() {

    private var _binding: FragmentStatsBinding? = null
    private val binding get() = _binding!!

    private val viewModel: StatsViewModel by viewModels()

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentStatsBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        setupTabs()
        setupChart()
        observeUiState()
    }

    private fun setupTabs() {
        binding.tabLayout.addOnTabSelectedListener(object : TabLayout.OnTabSelectedListener {
            override fun onTabSelected(tab: TabLayout.Tab?) {
                val period = when (tab?.position) {
                    0 -> StatsPeriod.TODAY
                    1 -> StatsPeriod.WEEK
                    2 -> StatsPeriod.MONTH
                    else -> StatsPeriod.WEEK
                }
                viewModel.setPeriod(period)
            }

            override fun onTabUnselected(tab: TabLayout.Tab?) {}
            override fun onTabReselected(tab: TabLayout.Tab?) {}
        })
    }

    private fun setupChart() {
        binding.barChart.apply {
            description.isEnabled = false
            setTouchEnabled(false)
            legend.isEnabled = false
            setDrawGridBackground(false)

            xAxis.apply {
                position = XAxis.XAxisPosition.BOTTOM
                setDrawGridLines(false)
                setDrawAxisLine(false)
                granularity = 1f
                labelRotationAngle = -45f
                textColor = resources.getColor(R.color.text_tertiary, null)
                textSize = 10f
            }

            axisLeft.apply {
                setDrawGridLines(true)
                gridColor = resources.getColor(R.color.chart_grid, null)
                setDrawAxisLine(false)
                axisMinimum = 0f
                textColor = resources.getColor(R.color.text_tertiary, null)
                textSize = 10f
            }

            axisRight.isEnabled = false

            setFitBars(true)
        }
    }

    private fun observeUiState() {
        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.uiState.collect { state ->
                    updateSummary(state)
                    updateChart(state)
                }
            }
        }
    }

    private fun updateSummary(state: StatsUiState) {
        binding.tvTotalScreenTime.text = TimeUtils.formatDuration(state.totalScreenTime)
        binding.tvSleepScreenTime.text = TimeUtils.formatDuration(state.totalSleepScreenTime)

        val periodText = when (state.period) {
            StatsPeriod.TODAY -> "今日"
            StatsPeriod.WEEK -> "本周"
            StatsPeriod.MONTH -> "本月"
        }
        binding.tvPeriodLabel.text = periodText
    }

    private fun updateChart(state: StatsUiState) {
        if (state.summaries.isEmpty()) {
            binding.barChart.clear()
            return
        }

        val entries = state.summaries.mapIndexed { index, summary ->
            BarEntry(index.toFloat(), summary.totalScreenMs / (1000f * 60f))
        }

        val labels = state.summaries.map { it.date.takeLast(5) }

        val dataSet = BarDataSet(entries, "亮屏时长").apply {
            color = resources.getColor(R.color.chart_primary, null)
            setDrawValues(false)
        }

        binding.barChart.xAxis.valueFormatter = IndexAxisValueFormatter(labels)
        binding.barChart.data = BarData(dataSet).apply {
            barWidth = 0.5f
        }
        binding.barChart.invalidate()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
